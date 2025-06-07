"""
llm_functions.py
Functions related to LLM interactions.
This module provides functions to detect the tone of a message.
"""
import os
import json
import re
from dotenv import load_dotenv
from google import genai
from typing import List
from google.genai import types
from pydantic import BaseModel
# from openai import OpenAI

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
# openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ToneDetectionResponse(BaseModel):
    """
    Represents the response schema for tone detection.
    """
    original_message: str
    tone: str
    explanation: str
    urgency: str
    confidence: int
    quick_replies: List[str]


class ModelConfig:
    """
    Configuration for the model to be used in tone detection.
    This class encapsulates the model name and system instruction.
    """
    DETECT_TONE_CONFIG = types.GenerateContentConfig(
        system_instruction = """
        You are a tone and urgency detection model for neurodivergent users.
        Analyze the following message and return:
        - include the original message as "original_message" in the JSON output.
        - the tone of the message (choose one: 'positive', 'negative', 'neutral', 'angry', 'sad', 'happy', 'confused', 'excited'),
        - a concise explanation (maximum 2 sentences),
        - whether the message is urgent or not (choose one: 'urgent', 'not urgent')
        - your confidence in your answer as a percentage (0-100), where 100 means absolutely certain and 0 means not confident at all.
        - and 3 quick, context-appropriate reply suggestions the user could send in response to the message. Each reply should have 40 characters maximum.

        Return your answer in this strict JSON format:
        {"original_message": "...",
         "tone": "...", 
         "explanation": "...", 
         "urgency": "...", 
         "confidence": ..., 
         "quick_replies": ["...", "...", "..."]
         }

        Examples:
       - "Can you please respond ASAP? This is important." → {
         "tone": "neutral",
         "explanation": "The message is a request with urgency.",
         "urgency": "urgent",
         "confidence": 92,
         "quick_replies": [
           "I'm on it and will get back to you ASAP.",
           "Received, I'll update you shortly.",
           "I'll prioritize this and respond soon."
         ]
         - "Hey, just checking in about the meeting next week." → {
        "tone": "neutral",
        "explanation": "The message is a casual inquiry.",
        "urgency": "not urgent",
        "confidence": 95,
        "quick_replies": [
          "Yes, the meeting is still on.",
          "Let me confirm and get back to you.",
          "Thanks for the reminder!"
         ]
         }
           """,
        max_output_tokens=200,
        temperature=0.4,
        top_p=0.8,
        top_k=20,
        response_schema=ToneDetectionResponse,
        response_mime_type="application/json"
    )

def extract_json(text):
    # Extract the first JSON object from the text
    match = re.search(r'\{.*?\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return None

def detect_tone(text: str) -> dict:
    prompt = f"Message: \"{text}\""
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",  # Use a stronger model if available
        config=ModelConfig.DETECT_TONE_CONFIG,  # Update this config to use the new instruction above
        contents=prompt
    )
    json_str = extract_json(response.text)
    if json_str:
        try:
            response_dict = json.loads(json_str)
            allowed_tones = ['positive', 'negative', 'neutral', 'angry', 'sad', 'happy', 'confused', 'excited']
            allowed_urgency = ['urgent', 'not urgent']
            if response_dict.get("tone") not in allowed_tones:
                return {"error": "Invalid tone detected", "raw_response": response.text}
            if response_dict.get("urgency") not in allowed_urgency:
                return {"error": "Invalid urgency detected", "raw_response": response.text}
            confidence = response_dict.get("confidence")
            try:
                confidence_val = int(confidence)
            except (ValueError, TypeError):
                return {"error": "Confidence is not a valid integer", "raw_response": response.text}
            if not (0 <= confidence_val <= 100):
                return {"error": "Invalid confidence value", "raw_response": response.text}
            # Optionally, you can replace the string/int in the dict with the validated int
            response_dict["confidence"] = confidence_val
            quick_replies = response_dict.get("quick_replies")
            if not (isinstance(quick_replies, list) and len(quick_replies) == 3 and all(isinstance(q, str) for q in quick_replies)):
                return {"error": "Invalid quick_replies value", "raw_response": response.text}
            response_dict["original_message"] = text  # Ensure original message is included
        except Exception:
            return {"error": "JSON parsing failed", "raw_response": response.text}
    else:
        return {"error": "No JSON found", "raw_response": response.text}
    return response_dict

def translate_to_greek_with_tone(original_message):
    """
    Translates the original message to Greek, preserving tone, emotion, and urgency.
    Uses Gemini (or OpenAI) for context-aware translation.
    """
    prompt = (
        "Translate the following message to Greek, preserving the tone, emotion, and urgency. "
        "Return ONLY the translated Greek sentence, with no explanation, no romanization, and no extra text. "
        "Message: " + original_message
    )
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=prompt
    )
    return response.text.strip()

def summarize_conversation(messages):
    """
    Summarizes a list of Slack messages using the LLM.
    """
    # Format messages for the prompt
    conversation = "\n".join(
        [f"{m.get('user', 'Someone')}: {m.get('text', '')}" for m in messages]
    )
    prompt = (
        "Summarize the following Slack thread. "
        "List key takeaways and any action items or decisions. Be concise.\n"
        f"Thread:\n{conversation}"
    )
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=prompt
    )
    return response.text.strip()

