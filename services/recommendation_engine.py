"""
Recommendation Engine - Investment recommendation formulas
Implements the formulas specified in CLAUDE.md
"""
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta

from db import fetch_all, fetch_one


def calculate_price_score(prices: List[Dict[str, Any]]) -> float:
    """
    Calculate price score based on 60-day price history.

    Formula:
    AvgP1 = Σ(i=0 to 30) fp(t-i) / 30          // Last 30 days average
    AvgP2 = Σ(i=30 to 60) fp(t-i) / 30         // Previous 30 days average
    Pc = (AvgP1 - AvgP2) / AvgP2               // Price change
    Ps = 50 + (50 × Pc)                         // Price score

    Returns:
        Price score (0-100)
    """
    if len(prices) < 60:
        return 50.0  # Neutral score if insufficient data

    # Sort by date descending (most recent first)
    prices_sorted = sorted(prices, key=lambda x: x['date'], reverse=True)

    # Last 30 days average
    avg_p1 = sum(p['close_price'] for p in prices_sorted[0:30]) / 30

    # Previous 30 days average
    avg_p2 = sum(p['close_price'] for p in prices_sorted[30:60]) / 30

    if avg_p2 == 0:
        return 50.0  # Avoid division by zero

    # Price change percentage
    price_change = (avg_p1 - avg_p2) / avg_p2

    # Price score
    price_score = 50 + (50 * price_change)

    # Clamp to 0-100
    return max(0, min(100, price_score))


def calculate_financial_score(statements: List[Dict[str, Any]]) -> float:
    """
    Calculate financial score based on revenue trends.

    Formula:
    Fs = 50 + (50 × (r(t) + r(t-1)) / r(t-1))

    Returns:
        Financial score (0-100)
    """
    if len(statements) < 2:
        return 50.0  # Neutral score if insufficient data

    # Sort by period_end_date descending (most recent first)
    statements_sorted = sorted(statements, key=lambda x: x['period_end_date'], reverse=True)

    r_current = statements_sorted[0]['revenue']
    r_previous = statements_sorted[1]['revenue']

    if r_previous == 0:
        return 50.0  # Avoid division by zero

    # Financial score
    financial_score = 50 + (50 * (r_current - r_previous) / r_previous)

    # Clamp to 0-100
    return max(0, min(100, financial_score))


def calculate_sentiment_score(db, company_id: int = None, asset_id: int = None) -> Tuple[float, float]:
    """
    Calculate average sentiment score and confidence for the last 30 days.

    Formula:
    Sc = Σ(i=0 to 30) s(t-i) / 30              // Last 30 days average sentiment
    AvgConf = Σ(i=0 to 30) cf(t-i) / 30        // Average confidence

    Returns:
        (sentiment_score, average_confidence)
    """
    # Fetch sentiment data from last 30 days
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
        return 0.0, 0.0  # Neutral if no data

    # Calculate averages
    avg_sentiment = sum(s['sentiment_score'] for s in sentiments) / len(sentiments)
    avg_confidence = sum(s['confidence_level'] for s in sentiments) / len(sentiments)

    # Convert sentiment score from -1..1 to 0..100
    sentiment_score = 50 + (50 * avg_sentiment)

    return sentiment_score, avg_confidence


def calculate_company_recommendation_no_ai(db, company_id: int) -> Dict[str, Any]:
    """
    Calculate investment recommendation WITHOUT AI (Price + Financial only).

    Formula:
    Is = (0.5 × Ps) + (0.5 × Fs)

    If Is ≥ 60 → Invest
    If Is ≥ 40 → Hold
    If Is < 40 → Don't Invest
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

    # Get financial statements
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

    # Calculate scores
    ps = calculate_price_score(prices)
    fs = calculate_financial_score(statements)

    # Investment score
    investment_score = (0.5 * ps) + (0.5 * fs)

    # Determine recommendation type
    if investment_score >= 60:
        recommendation_type = "invest"
    elif investment_score >= 40:
        recommendation_type = "hold"
    else:
        recommendation_type = "dont_invest"

    # Determine risk level (simplified without sentiment)
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

    Formula:
    If AvgConf > 0.5:
        Is = (0.3 × Ps) + (0.3 × Fs) + (0.4 × Sc)
    Else:
        Is = (0.4 × Ps) + (0.4 × Fs) + (0.2 × Sc)

    Risk Level:
    If Sc < 40 OR Fs < 30 → High Risk
    If Sc > 70 AND Fs > 60 → Low Risk
    Else → Medium Risk

    Recommendation:
    If Is ≥ 70 → Invest (Strong)
    If Is ≥ 55 → Invest (Moderate)
    If Is ≥ 40 → Hold
    If Is < 40 → Don't Invest
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

    # Get financial statements
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

    # Calculate scores
    ps = calculate_price_score(prices)
    fs = calculate_financial_score(statements)
    sc, avg_conf = calculate_sentiment_score(db, company_id=company_id)

    # Investment score with dynamic weighting
    if avg_conf > 0.5:
        investment_score = (0.3 * ps) + (0.3 * fs) + (0.4 * sc)
    else:
        investment_score = (0.4 * ps) + (0.4 * fs) + (0.2 * sc)

    # Determine risk level
    if sc < 40 or fs < 30:
        risk_level = "high"
    elif sc > 70 and fs > 60:
        risk_level = "low"
    else:
        risk_level = "medium"

    # Determine recommendation type
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

    Formula:
    If AvgConf > 0.5:
        Is = (0.5 × Ps) + (0.5 × Sc)
    Else:
        Is = (0.7 × Ps) + (0.3 × Sc)
    """
    # Get price history
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

    # Calculate scores
    ps = calculate_price_score(prices)
    sc, avg_conf = calculate_sentiment_score(db, asset_id=asset_id)

    # Investment score with dynamic weighting
    if avg_conf > 0.5:
        investment_score = (0.5 * ps) + (0.5 * sc)
    else:
        investment_score = (0.7 * ps) + (0.3 * sc)

    # Determine recommendation type (same thresholds as companies)
    if investment_score >= 70:
        recommendation_type = "invest"
    elif investment_score >= 55:
        recommendation_type = "invest"
    elif investment_score >= 40:
        recommendation_type = "hold"
    else:
        recommendation_type = "dont_invest"

    # Determine risk level (simplified for assets)
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