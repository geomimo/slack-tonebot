"""
llm_functions.py
Functions related to LLM interactions.
This module provides functions to detect the tone of a message.
"""
import os
import json
from typing import List
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, field_validator
from enum import Enum
# from openai import OpenAI

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
# openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gemini-2.0-flash-lite"  # Use a stronger model if available

class AllowedTones(str, Enum):
    """
    Enum for allowed tones in tone detection.
    """
    POSITIVE = 'positive'
    NEGATIVE = 'negative'
    NEUTRAL = 'neutral'
    ANGRY = 'angry'
    SAD = 'sad'
    HAPPY = 'happy'
    CONFUSED = 'confused'
    EXCITED = 'excited'

class AllowedUrgency(str, Enum):
    """
    Enum for allowed urgency levels in tone detection.
    """
    URGENT = 'urgent'
    NOT_URGENT = 'not urgent'


class ToneDetectionResponse(BaseModel):
    """
    Represents the response schema for tone detection.
    """
    original_message: str
    tone: AllowedTones
    explanation: str
    urgency: AllowedUrgency
    confidence: int
    quick_replies: List[str]

    @field_validator('quick_replies')
    @classmethod
    def must_have_three_items(cls, v):
        if len(v) != 3:
            raise ValueError('my_field must have exactly 3 string elements')
        return v
    
    @classmethod
    def from_json(cls, json_str: str):
        """
        Parses a JSON string into a ToneDetectionResponse object.
        """
        return cls.model_validate_json(json_str)
    
    def __str__(self):
        return (
            f"Original Message: {self.original_message}\n"
            f"Tone: {self.tone.value}\n"
            f"Explanation: {self.explanation}\n"
            f"Urgency: {self.urgency.value}\n"
            f"Confidence: {self.confidence}%\n"
            f"Quick Replies: {self.quick_replies}"
        )

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



def detect_tone(text: str) -> str:
    """
    Detects the tone and urgency of a given message using the Gemini API.

    Args:
        text (str): The message to analyze.

    Returns:
        ToneDetectionResponse: The structured response containing the original message, detected tone, explanation, urgency, confidence, and quick reply suggestions.
    """


    prompt = f"Message: \"{text}\""
    response = client.models.generate_content(
        model=MODEL,
        config=ModelConfig.DETECT_TONE_CONFIG,
        contents=prompt
    )
    json_str = json.loads(response.text)
    if not json_str or json_str == "":
        return {"error": "Empty response from the model", "raw_response": response.text}
    
    response_model = ToneDetectionResponse.from_json(response.text)

    return response_model


def translate_to_greek_with_tone(text):
    """
    Translates the original message to Greek, preserving tone, emotion, and urgency.
    Uses Gemini (or OpenAI) for context-aware translation.
    """
    prompt = (
        "Translate the following message to Greek, preserving the tone, emotion, and urgency. "
        "Return ONLY the translated Greek sentence, with no explanation, no romanization, and no extra text. "
        "Message: " + text
    )
    response = client.models.generate_content(
        model=MODEL,
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
        model=MODEL,
        contents=prompt
    )