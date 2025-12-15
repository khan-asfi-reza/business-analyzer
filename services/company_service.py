"""
Company service - Company data business logic
"""
from typing import Optional, Dict, Any, List
import humanize

from db import fetch_one, fetch_all
from utils.helpers import humanize_date


def get_company_by_id(db, company_id: int) -> Optional[Dict[str, Any]]:
    """Get company details by ID"""
    data = fetch_one(
        db,
        """
        SELECT company_id, company_name, company_type, industry,
               logo_url, founded_date, description, market_cap
        FROM company
        WHERE company_id = %s
        """,
        (company_id,)
    )
    if data and data["market_cap"]:
        data["market_cap"] = humanize.intword(data["market_cap"])

    return data



def search_companies(db, query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Search companies by name or industry"""
    return fetch_all(
        db,
        """
        SELECT company_id, company_name, company_type, industry, logo_url
        FROM company
        WHERE company_name LIKE %s OR industry LIKE %s
        LIMIT %s
        """,
        (f"%{query}%", f"%{query}%", limit)
    )


def get_latest_stock_price(db, company_id: int) -> Optional[Dict[str, Any]]:
    """Get the most recent stock price for a company"""
    return fetch_one(
        db,
        """
        SELECT price_id, date, close_price, currency, volume
        FROM stock_price
        WHERE company_id = %s
        ORDER BY date DESC
        LIMIT 1
        """,
        (company_id,)
    )


def get_stock_prices(db, company_id: int, days: int = 60) -> List[Dict[str, Any]]:
    """Get stock price history for specified number of days"""
    data = fetch_all(
        db,
        """
        SELECT date, open_price, close_price, high_price, low_price, volume, currency
        FROM stock_price
        WHERE company_id = %s AND date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        ORDER BY date DESC
        """,
        (company_id, days)
    )
    for item in data:
        item["date"] = humanize_date(item["date"])
        for key in ["open_price","close_price", "high_price", "low_price"]:
            item[key] = float(item[key])
    return data




def get_latest_financial_statement(db, company_id: int) -> Optional[Dict[str, Any]]:
    """Get the most recent financial statement for a company"""
    return fetch_one(
        db,
        """
        SELECT statement_id, statement_type, period_start_date, period_end_date,
               revenue, profit, currency
        FROM financial_statement
        WHERE company_id = %s
        ORDER BY period_end_date DESC
        LIMIT 1
        """,
        (company_id,)
    )


def get_financial_statements(db, company_id: int, limit: int = 8) -> List[Dict[str, Any]]:
    """Get recent financial statements for a company"""
    return fetch_all(
        db,
        """
        SELECT statement_type, period_start_date, period_end_date,
               revenue, profit, currency
        FROM financial_statement
        WHERE company_id = %s
        ORDER BY period_end_date DESC
        LIMIT %s
        """,
        (company_id, limit)
    )


def get_company_recommendation(db, company_id: int) -> Optional[Dict[str, Any]]:
    """Get the latest investment recommendation for a company"""
    return fetch_one(
        db,
        """
        SELECT recommendation_type, investment_score, risk_level,
               expected_return, rationale_summary, recommendation_date
        FROM investment_recommendation
        WHERE company_id = %s
        ORDER BY recommendation_date DESC
        LIMIT 1
        """,
        (company_id,)
    )