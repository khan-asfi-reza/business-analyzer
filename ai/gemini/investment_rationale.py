import json
import re
from typing import Dict, Any, Optional
from google.genai import types

from .config import get_gemini_client, get_generation_config, DEFAULT_GEMINI_MODEL
from prompts import PROMPT_INVESTMENT_RATIONALE


def generate_investment_rationale(
    name: str,
    recommendation_type: str,
    risk_level: str,
    investment_score: float,
    price_trend: str,
    financial_health: str,
    sentiment: str,
    api_key: Optional[str] = None,
    model_name: str = DEFAULT_GEMINI_MODEL
) -> Dict[str, Any]:
    """
    Generate investment rationale based on analysis data using Gemini

    """
    try:
        client = get_gemini_client(api_key=api_key)

        prompt = PROMPT_INVESTMENT_RATIONALE.format(
            name=name,
            recommendation_type=recommendation_type,
            risk_level=risk_level,
            investment_score=investment_score,
            price_trend=price_trend,
            financial_health=financial_health,
            sentiment=sentiment
        )
        json_instruction = """

Return your response in the following JSON format ONLY (no markdown, no extra text):
{
    "rationale": "2-3 sentence explanation of the recommendation",
    "key_factors": ["factor1", "factor2", "factor3"],
    "warnings": ["warning1", "warning2"],
    "timeframe": "short-term/medium-term/long-term",
    "confidence": "high/medium/low"
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

        timeframe = result.get("timeframe", "medium-term").lower()
        if timeframe not in ["short-term", "medium-term", "long-term"]:
            timeframe = "medium-term"

        confidence = result.get("confidence", "medium").lower()
        if confidence not in ["high", "medium", "low"]:
            confidence = "medium"

        return {
            "rationale": result.get("rationale", "Rationale not available"),
            "key_factors": result.get("key_factors", []),
            "warnings": result.get("warnings", []),
            "timeframe": timeframe,
            "confidence": confidence,
            "error": None
        }

    except json.JSONDecodeError as e:
        return {
            "rationale": f"Based on {recommendation_type} recommendation with {risk_level} risk.",
            "key_factors": [],
            "warnings": [],
            "timeframe": "medium-term",
            "confidence": "low",
            "error": f"Failed to parse JSON response: {str(e)}"
        }

    except Exception as e:
        return {
            "rationale": f"Based on {recommendation_type} recommendation with {risk_level} risk.",
            "key_factors": [],
            "warnings": [],
            "timeframe": "medium-term",
            "confidence": "low",
            "error": f"Investment rationale generation failed: {str(e)}"
        }