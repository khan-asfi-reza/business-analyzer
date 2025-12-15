import os
from typing import Optional
from google import genai

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"

def get_gemini_client(api_key: Optional[str] = None):
    key = api_key or os.getenv("GEMINI_API_KEY")

    if not key:
        raise ValueError(
            "Gemini API key not found. Set GEMINI_API_KEY environment variable "
            "or pass api_key parameter."
        )

    client = genai.Client(api_key=key)
    return client


def get_generation_config():
    return {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 2048,
    }