import json
import re
from typing import Dict, Any, Optional
from google.genai import types
from .config import get_gemini_client, get_generation_config, DEFAULT_GEMINI_MODEL
from prompts import PROMPT_COMPANY_ANALYSIS


def analyze_company(
    company_name: str,
    industry: str,
    news_summary: str,
    financial_summary: str,
    api_key: Optional[str] = None,
    model_name: str = DEFAULT_GEMINI_MODEL
) -> Dict[str, Any]:
    """
    Generate company analysis using Gemini
    """
    try:
        client = get_gemini_client(api_key=api_key)
        prompt = PROMPT_COMPANY_ANALYSIS.format(
            company_name=company_name,
            industry=industry,
            news_summary=news_summary,
            financial_summary=financial_summary
        )
        json_instruction = """
Return your response in the following JSON format ONLY (no markdown, no extra text):
{
    "analysis": "Brief 3-5 sentence analysis",
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "market_position": "Description of market position",
    "growth_potential": "Assessment of growth potential",
    "key_risks": ["risk1", "risk2"]
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

        return {
            "analysis": result.get("analysis", "Analysis not available"),
            "strengths": result.get("strengths", []),
            "weaknesses": result.get("weaknesses", []),
            "market_position": result.get("market_position", "Unknown"),
            "growth_potential": result.get("growth_potential", "Unknown"),
            "key_risks": result.get("key_risks", []),
            "error": None
        }

    except json.JSONDecodeError as e:
        return {
            "analysis": "Failed to generate analysis",
            "strengths": [],
            "weaknesses": [],
            "market_position": "Unknown",
            "growth_potential": "Unknown",
            "key_risks": [],
            "error": f"Failed to parse JSON response: {str(e)}"
        }

    except Exception as e:
        return {
            "analysis": "Failed to generate analysis",
            "strengths": [],
            "weaknesses": [],
            "market_position": "Unknown",
            "growth_potential": "Unknown",
            "key_risks": [],
            "error": f"Company analysis failed: {str(e)}"
        }