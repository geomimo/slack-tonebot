# """
# llm_functions.py
# Functions related to LLM interactions.
# This module provides functions to detect the tone of a message using OpenAI's API.
# """
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import json
from pydantic import BaseModel

# from openai import OpenAI

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
# openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ToneDetectionResponse(BaseModel):
    """
    Represents the response schema for tone detection.
    """
    tone: str
    explanation: str

class ModelConfig:
    """
    Configuration for the model to be used in tone detection.
    This class encapsulates the model name and system instruction.
    """
    DETECT_TONE_CONFIG = types.GenerateContentConfig(
        system_instruction="""You are a tone detection model for neurodivergent users.
        Analyze the text and return the tone of the message with a short explanation.
        The tone should be one of the following: 'positive', 'negative', 
        'neutral', 'angry', 'sad', 'happy', 'confused', 'excited'. Output example {"tone": 
        "positive", "explanation": "The message expresses a positive sentiment."}""",
        max_output_tokens=100,
        temperature=0.5,
        top_p=0.9,
        top_k=40,
        response_schema=ToneDetectionResponse,
        response_mime_type="application/json"
    )



def detect_tone(text: str) -> str:
    """
    Detects the tone of a given message using OpenAI's API.
    
    Args:
        message (str): The message to analyze.
        
    Returns:
        str: The detected tone of the message.
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        config=ModelConfig.DETECT_TONE_CONFIG,
        contents=text
    )

    try:
        response_dict = json.loads(response.text)
    except json.JSONDecodeError:
        response_dict = {"error": "Invalid JSON response", "raw_response": response.text}

    return response_dict
