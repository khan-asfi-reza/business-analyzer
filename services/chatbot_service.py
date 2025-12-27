"""
Chatbot service - AI-powered company Q&A
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from db import fetch_one, fetch_all, execute
from services.company_service import (
    get_company_by_id,
    get_latest_stock_price,
    get_stock_prices,
    get_latest_financial_statement,
    get_financial_statements,
    get_company_recommendation
)


def get_company_context(db, company_id: int) -> Dict[str, Any]:
    """
    Gather all available company data for chatbot context
    """
    company = get_company_by_id(db, company_id)
    if not company:
        return None

    latest_price = get_latest_stock_price(db, company_id)
    price_history = get_stock_prices(db, company_id, days=30)
    latest_financial = get_latest_financial_statement(db, company_id)
    financial_history = get_financial_statements(db, company_id, limit=4)
    recommendation = get_company_recommendation(db, company_id)
    sentiment_data = get_recent_sentiment(db, company_id)

    stock_price_summary = format_stock_price_summary(latest_price, price_history)
    financial_summary = format_financial_summary(latest_financial, financial_history)
    sentiment_summary = format_sentiment_summary(sentiment_data)
    recommendation_summary = format_recommendation_summary(recommendation)

    return {
        "company_name": company.get("company_name", "N/A"),
        "industry": company.get("industry", "N/A"),
        "company_type": company.get("company_type", "N/A"),
        "founded_date": str(company.get("founded_date", "N/A")),
        "market_cap": company.get("market_cap", "N/A"),
        "description": company.get("description", "No description available"),
        "stock_price_summary": stock_price_summary,
        "financial_summary": financial_summary,
        "sentiment_summary": sentiment_summary,
        "recommendation_summary": recommendation_summary
    }


def get_recent_sentiment(db, company_id: int, days: int = 30) -> List[Dict[str, Any]]:
    """
    Get recent sentiment analysis results for company-related content
    """
    return fetch_all(
        db,
        """
        SELECT sa.sentiment_label, sa.sentiment_score, sa.confidence_level,
               sc.title, sc.publish_date
        FROM sentiment_analysis sa
        JOIN scraped_content sc ON sa.content_id = sc.content_id
        WHERE sc.company_id = %s
          AND sc.publish_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        ORDER BY sc.publish_date DESC
        LIMIT 10
        """,
        (company_id, days)
    )


def format_stock_price_summary(latest_price: Optional[Dict], price_history: List[Dict]) -> str:
    """
    Format stock price data into readable text
    """
    if not latest_price:
        return "No stock price data available"

    summary = f"Latest Close: {latest_price['close_price']} {latest_price['currency']} (Date: {latest_price['date']})"

    if price_history and len(price_history) > 1:
        avg_price = sum(p['close_price'] for p in price_history) / len(price_history)
        summary += f"\n30-day Average: {avg_price:.2f} {latest_price['currency']}"

        oldest_price = float(price_history[-1]['close_price'])
        change_pct = ((float(latest_price['close_price']) - float(oldest_price)) / float(oldest_price)) * 100
        summary += f"\n30-day Change: {change_pct:+.2f}%"

    return summary


def format_financial_summary(latest: Optional[Dict], history: List[Dict]) -> str:
    """
    Format financial statement data into readable text
    """
    if not latest:
        return "No financial data available"

    summary = f"Latest Period ({latest['statement_type']}): {latest['period_start_date']} to {latest['period_end_date']}"
    summary += f"\nRevenue: {latest['revenue']} {latest['currency']}"
    summary += f"\nProfit: {latest['profit']} {latest['currency']}"

    if history and len(history) > 1:
        prev = history[1]
        if prev['revenue']:
            revenue_change = ((latest['revenue'] - prev['revenue']) / prev['revenue']) * 100
            summary += f"\nRevenue Growth: {revenue_change:+.2f}% from previous period"

    return summary


def format_sentiment_summary(sentiment_data: List[Dict]) -> str:
    """
    Format sentiment analysis data into readable text
    """
    if not sentiment_data:
        return "No sentiment data available"

    positive = sum(1 for s in sentiment_data if s['sentiment_label'] == 'positive')
    negative = sum(1 for s in sentiment_data if s['sentiment_label'] == 'negative')
    neutral = sum(1 for s in sentiment_data if s['sentiment_label'] == 'neutral')

    avg_score = sum(s['sentiment_score'] for s in sentiment_data) / len(sentiment_data)

    summary = f"Recent News Sentiment (last 30 days): {len(sentiment_data)} articles analyzed"
    summary += f"\nPositive: {positive}, Neutral: {neutral}, Negative: {negative}"
    summary += f"\nAverage Sentiment Score: {avg_score:.2f} (range: -1 to +1)"

    return summary


def format_recommendation_summary(recommendation: Optional[Dict]) -> str:
    """
    Format investment recommendation into readable text
    """
    if not recommendation:
        return "No AI recommendation available yet"

    summary = f"Recommendation: {recommendation['recommendation_type'].upper()}"
    summary += f"\nRisk Level: {recommendation['risk_level'].upper()}"
    summary += f"\nInvestment Score: {recommendation['investment_score']:.2f}/100"

    if recommendation.get('expected_return'):
        summary += f"\nExpected Return: {recommendation['expected_return']}%"

    if recommendation.get('rationale_summary'):
        summary += f"\nRationale: {recommendation['rationale_summary']}"

    summary += f"\nAnalysis Date: {recommendation['recommendation_date']}"

    return summary


def save_chat_message(
    db,
    user_id: int,
    company_id: int,
    session_id: str,
    message_text: str,
    is_user_message: bool
) -> int:
    """
    Store a chat message in the database
    """
    result = execute(
        db,
        """
        INSERT INTO chat_message
        (user_id, company_id, conversation_session_id, message_text, is_user_message)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, company_id, session_id, message_text, is_user_message)
    )
    db.commit()
    return result


def get_chat_history(
    db,
    user_id: int,
    company_id: int,
    session_id: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Retrieve chat history for a user and company
    """
    if session_id:
        return fetch_all(
            db,
            """
            SELECT chat_message_id, message_text, is_user_message, created_at
            FROM chat_message
            WHERE user_id = %s AND company_id = %s AND conversation_session_id = %s
            ORDER BY created_at ASC
            LIMIT %s
            """,
            (user_id, company_id, session_id, limit)
        )
    else:
        return fetch_all(
            db,
            """
            SELECT chat_message_id, message_text, is_user_message, created_at,
                   conversation_session_id
            FROM chat_message
            WHERE user_id = %s AND company_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (user_id, company_id, limit)
        )


def create_session_id() -> str:
    """
    Generate a unique session ID for a chat conversation
    """
    return str(uuid.uuid4())