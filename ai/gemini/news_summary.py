import json
import re
from typing import Dict, Any, Optional
from google.genai import types
from .config import get_gemini_client, get_generation_config, DEFAULT_GEMINI_MODEL
from prompts import PROMPT_NEWS_SUMMARY


def summarize_news(
    article_text: str,
    api_key: Optional[str] = None,
    model_name: str = DEFAULT_GEMINI_MODEL
) -> Dict[str, Any]:
    """
    Summarize financial news article using Gemini

    """
    response_text = ""
    try:
        client = get_gemini_client(api_key=api_key)

        prompt = PROMPT_NEWS_SUMMARY.format(article_text=article_text)

        json_instruction = """

Also extract key information and return in the following JSON format ONLY (no markdown, no extra text):
{
    "summary": "2-3 sentence summary",
    "key_points": ["point1", "point2", "point3"],
    "companies_mentioned": ["Company A", "Company B"],
    "sentiment_hint": "positive/negative/neutral"
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

        sentiment_hint = result.get("sentiment_hint", "neutral").lower()
        if sentiment_hint not in ["positive", "negative", "neutral"]:
            sentiment_hint = "neutral"

        return {
            "summary": result.get("summary", "Summary not available"),
            "key_points": result.get("key_points", []),
            "companies_mentioned": result.get("companies_mentioned", []),
            "sentiment_hint": sentiment_hint,
            "error": None
        }

    except json.JSONDecodeError as e:
        return {
            "summary": response_text[:500] if response_text else "Summary not available",
            "key_points": [],
            "companies_mentioned": [],
            "sentiment_hint": "neutral",
            "error": f"Failed to parse JSON response: {str(e)}"
        }

    except Exception as e:
        return {
            "summary": "Failed to generate summary",
            "key_points": [],
            "companies_mentioned": [],
            "sentiment_hint": "neutral",
            "error": f"News summarization failed: {str(e)}"
        }