"""
Gemini AI Provider Functions
All functions return JSON-serializable dictionaries for easy use in Celery tasks.
"""
from .sentiment import classify_sentiment
from .company_analysis import analyze_company
from .news_summary import summarize_news
from .investment_rationale import generate_investment_rationale
from .config import get_gemini_client, get_generation_config

__all__ = [
    "classify_sentiment",
    "analyze_company",
    "summarize_news",
    "generate_investment_rationale",
    "get_gemini_client",
    "get_generation_config",
]