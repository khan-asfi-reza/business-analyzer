from typing import Dict, Any, List, Tuple

from db import fetch_all


def calculate_price_score(prices: List[Dict[str, Any]]) -> float:
    """
    Calculate price score based on 60-day price history.

    Returns:
        Price score (0-100)
    """
    if len(prices) < 60:
        return 50.0
    prices_sorted = sorted(prices, key=lambda x: x['date'], reverse=True)

    avg_p1 = sum(p['close_price'] for p in prices_sorted[0:30]) / 30

    avg_p2 = sum(p['close_price'] for p in prices_sorted[30:60]) / 30

    if avg_p2 == 0:
        return 50.0

    price_change = (avg_p1 - avg_p2) / avg_p2

    price_score = 50 + (50 * price_change)

    return max(0, min(100, price_score))


def calculate_financial_score(statements: List[Dict[str, Any]]) -> float:
    """
    Calculate financial score based on revenue trends.

    """
    if len(statements) < 2:
        return 50.0  # Neutral score if insufficient data

    statements_sorted = sorted(statements, key=lambda x: x['period_end_date'], reverse=True)
    r_current = statements_sorted[0]['revenue']
    r_previous = statements_sorted[1]['revenue']
    if r_previous == 0:
        return 50.0
    financial_score = 50 + (50 * (r_current - r_previous) / r_previous)

    return max(0, min(100, financial_score))


def calculate_sentiment_score(db, company_id: int = None, asset_id: int = None) -> Tuple[float, float]:
    """
    Calculate average sentiment score and confidence for the last 30 days.

    Returns:
        (sentiment_score, average_confidence)
    """
    sentiments = fetch_all(
        db,
        """
        SELECT sa.sentiment_score, sa.confidence_level
        FROM sentiment_analysis sa
        JOIN scraped_content sc ON sa.content_id = sc.content_id
        WHERE sc.company_id = %s
          AND sc.publish_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """,
        (company_id,) if company_id else (asset_id,)
    )

    if not sentiments:
        return 0.0, 0.0
    avg_sentiment = sum(s['sentiment_score'] for s in sentiments) / len(sentiments)
    avg_confidence = sum(s['confidence_level'] for s in sentiments) / len(sentiments)

    sentiment_score = 50 + (50 * avg_sentiment)

    return sentiment_score, avg_confidence


def calculate_company_recommendation_no_ai(db, company_id: int) -> Dict[str, Any]:
    """
    Calculate investment recommendation WITHOUT AI (Price + Financial only).

    """
    prices = fetch_all(
        db,
        """
        SELECT date, close_price
        FROM stock_price
        WHERE company_id = %s AND date >= DATE_SUB(CURDATE(), INTERVAL 60 DAY)
        ORDER BY date DESC
        """,
        (company_id,)
    )

    statements = fetch_all(
        db,
        """
        SELECT period_end_date, revenue
        FROM financial_statement
        WHERE company_id = %s
        ORDER BY period_end_date DESC
        LIMIT 2
        """,
        (company_id,)
    )

    ps = calculate_price_score(prices)
    fs = calculate_financial_score(statements)

    investment_score = (0.5 * ps) + (0.5 * fs)

    if investment_score >= 60:
        recommendation_type = "invest"
    elif investment_score >= 40:
        recommendation_type = "hold"
    else:
        recommendation_type = "dont_invest"

    if fs < 30:
        risk_level = "high"
    elif fs > 60:
        risk_level = "low"
    else:
        risk_level = "medium"

    return {
        "recommendation_type": recommendation_type,
        "investment_score": round(investment_score, 2),
        "risk_level": risk_level,
        "price_score": round(ps, 2),
        "financial_score": round(fs, 2)
    }


def calculate_company_recommendation_with_ai(db, company_id: int) -> Dict[str, Any]:
    """
    Calculate investment recommendation WITH AI (Price + Financial + Sentiment).

    """
    # Get price history
    prices = fetch_all(
        db,
        """
        SELECT date, close_price
        FROM stock_price
        WHERE company_id = %s AND date >= DATE_SUB(CURDATE(), INTERVAL 60 DAY)
        ORDER BY date DESC
        """,
        (company_id,)
    )

    statements = fetch_all(
        db,
        """
        SELECT period_end_date, revenue
        FROM financial_statement
        WHERE company_id = %s
        ORDER BY period_end_date DESC
        LIMIT 2
        """,
        (company_id,)
    )

    ps = calculate_price_score(prices)
    fs = calculate_financial_score(statements)
    sc, avg_conf = calculate_sentiment_score(db, company_id=company_id)

    if avg_conf > 0.5:
        investment_score = (0.3 * ps) + (0.3 * fs) + (0.4 * sc)
    else:
        investment_score = (0.4 * ps) + (0.4 * fs) + (0.2 * sc)

    if sc < 40 or fs < 30:
        risk_level = "high"
    elif sc > 70 and fs > 60:
        risk_level = "low"
    else:
        risk_level = "medium"

    if investment_score >= 70:
        recommendation_type = "invest"
    elif investment_score >= 55:
        recommendation_type = "invest"
    elif investment_score >= 40:
        recommendation_type = "hold"
    else:
        recommendation_type = "dont_invest"

    return {
        "recommendation_type": recommendation_type,
        "investment_score": round(investment_score, 2),
        "risk_level": risk_level,
        "price_score": round(ps, 2),
        "financial_score": round(fs, 2),
        "sentiment_score": round(sc, 2),
        "confidence_level": round(avg_conf, 2)
    }


def calculate_asset_recommendation(db, asset_id: int) -> Dict[str, Any]:
    """
    Calculate investment recommendation for assets (Price + Sentiment only, no financials).

    """
    prices = fetch_all(
        db,
        """
        SELECT date, price as close_price
        FROM asset_price
        WHERE asset_id = %s AND date >= DATE_SUB(CURDATE(), INTERVAL 60 DAY)
        ORDER BY date DESC
        """,
        (asset_id,)
    )

    ps = calculate_price_score(prices)
    sc, avg_conf = calculate_sentiment_score(db, asset_id=asset_id)

    if avg_conf > 0.5:
        investment_score = (0.5 * ps) + (0.5 * sc)
    else:
        investment_score = (0.7 * ps) + (0.3 * sc)

    if investment_score >= 70:
        recommendation_type = "invest"
    elif investment_score >= 55:
        recommendation_type = "invest"
    elif investment_score >= 40:
        recommendation_type = "hold"
    else:
        recommendation_type = "dont_invest"

    if sc < 40:
        risk_level = "high"
    elif sc > 70:
        risk_level = "low"
    else:
        risk_level = "medium"

    return {
        "recommendation_type": recommendation_type,
        "investment_score": round(investment_score, 2),
        "risk_level": risk_level,
        "price_score": round(ps, 2),
        "sentiment_score": round(sc, 2),
        "confidence_level": round(avg_conf, 2)
    }