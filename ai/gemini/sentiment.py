import json
import re
from typing import Dict, Any, Optional
from google.genai import types
from .config import get_gemini_client, get_generation_config, DEFAULT_GEMINI_MODEL
from prompts import PROMPT_SENTIMENT_CLASSIFICATION


def classify_sentiment(
    text: str,
    api_key: Optional[str] = None,
    model_name: str = DEFAULT_GEMINI_MODEL
) -> Dict[str, Any]:
    """
    Analyze sentiment of financial text using Gemini
    """
    try:
        client = get_gemini_client(api_key=api_key)
        prompt = PROMPT_SENTIMENT_CLASSIFICATION.format(text=text)
        json_instruction = """

Return your response in the following JSON format ONLY (no markdown, no extra text):
{
    "sentiment": "positive/negative/neutral",
    "score": -1.0 to +1.0,
    "confidence": 0.0 to 1.0
}
"""
        full_prompt = prompt + json_instruction
        response = client.models.generate_content(
            model=model_name,
            contents=full_prompt,
            config=types.GenerateContentConfig(**get_generation_config())
        )
        response_text = response.text.strip()
        json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
        result = json.loads(response_text)

        sentiment_label = result.get("sentiment", "neutral").lower()
        if sentiment_label not in ["positive", "negative", "neutral"]:
            sentiment_label = "neutral"

        sentiment_score = float(result.get("score", 0.0))
        sentiment_score = max(-1.0, min(1.0, sentiment_score))  # Clamp to [-1, 1]

        confidence_level = float(result.get("confidence", 0.5))
        confidence_level = max(0.0, min(1.0, confidence_level))  # Clamp to [0, 1]

        return {
            "sentiment_label": sentiment_label,
            "sentiment_score": sentiment_score,
            "confidence_level": confidence_level,
            "error": None
        }

    except json.JSONDecodeError as e:
        return {
            "sentiment_label": "neutral",
            "sentiment_score": 0.0,
            "confidence_level": 0.0,
            "error": f"Failed to parse JSON response: {str(e)}"
        }

    except Exception as e:
        return {
            "sentiment_label": "neutral",
            "sentiment_score": 0.0,
            "confidence_level": 0.0,
            "error": f"Sentiment analysis failed: {str(e)}"
        }