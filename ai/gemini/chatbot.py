from typing import Dict, Any, Optional
from google.genai import types
from .config import get_gemini_client, get_generation_config, DEFAULT_GEMINI_MODEL
from prompts import PROMPT_COMPANY_CHATBOT


def answer_company_question(
    company_context: Dict[str, Any],
    user_question: str,
    api_key: Optional[str] = None,
    model_name: str = DEFAULT_GEMINI_MODEL
) -> Dict[str, Any]:
    """
    Answer user questions about a company using AI
    """
    try:
        client = get_gemini_client(api_key=api_key)

        prompt = PROMPT_COMPANY_CHATBOT.format(
            company_name=company_context.get("company_name", "N/A"),
            industry=company_context.get("industry", "N/A"),
            company_type=company_context.get("company_type", "N/A"),
            founded_date=company_context.get("founded_date", "N/A"),
            market_cap=company_context.get("market_cap", "N/A"),
            description=company_context.get("description", "N/A"),
            stock_price_summary=company_context.get("stock_price_summary", "N/A"),
            financial_summary=company_context.get("financial_summary", "N/A"),
            sentiment_summary=company_context.get("sentiment_summary", "N/A"),
            recommendation_summary=company_context.get("recommendation_summary", "N/A"),
            user_question=user_question
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(**get_generation_config())
        )

        answer = response.text.strip()

        return {
            "answer": answer,
            "error": None
        }

    except Exception as e:
        return {
            "answer": None,
            "error": f"Failed to generate answer: {str(e)}"
        }