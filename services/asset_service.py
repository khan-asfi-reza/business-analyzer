"""
Asset service - Asset data business logic
"""
import datetime
from typing import Optional, Dict, Any, List
import caseutil
from db import fetch_one, fetch_all
from utils.helpers import humanize_date


def get_asset_by_id(db, asset_id: int) -> Optional[Dict[str, Any]]:
    """Get asset details by ID"""
    data = fetch_one(
        db,
        """
        SELECT asset_id, asset_name, asset_type, unit_of_measurement,
               description, logo_url
        FROM asset
        WHERE asset_id = %s
        """,
        (asset_id,)
    )
    if data:
        if data["asset_type"]:
            data["asset_type"] = caseutil.to_sentence(data["asset_type"])

        if data["unit_of_measurement"]:
            data["unit_of_measurement"] = caseutil.to_sentence(data["unit_of_measurement"])

    return data

def search_assets(db, query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Search assets by name or type"""
    return fetch_all(
        db,
        """
        SELECT asset_id, asset_name, asset_type, unit_of_measurement
        FROM asset
        WHERE asset_name LIKE %s OR asset_type LIKE %s
        LIMIT %s
        """,
        (f"%{query}%", f"%{query}%", limit)
    )


def get_latest_asset_price(db, asset_id: int) -> Optional[Dict[str, Any]]:
    """Get the most recent price for an asset"""
    return fetch_one(
        db,
        """
        SELECT asset_price_id, date, price, currency
        FROM asset_price
        WHERE asset_id = %s
        ORDER BY date DESC
        LIMIT 1
        """,
        (asset_id,)
    )


def get_asset_prices(db, asset_id: int, days: int = 60) -> List[Dict[str, Any]]:
    """Get asset price history for specified number of days"""
    data = fetch_all(
        db,
        """
        SELECT date, price, currency
        FROM asset_price
        WHERE asset_id = %s AND date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        ORDER BY date DESC
        """,
        (asset_id, days)
    )
    for item in data:
        item["data"] = humanize_date(item["date"])
        item["price"] = float(item["price"])

    return data


def get_asset_recommendation(db, asset_id: int) -> Optional[Dict[str, Any]]:
    """Get the latest investment recommendation for an asset"""
    return fetch_one(
        db,
        """
        SELECT recommendation_type, investment_score, risk_level,
               expected_return, rationale_summary, recommendation_date
        FROM investment_recommendation
        WHERE asset_id = %s
        ORDER BY recommendation_date DESC
        LIMIT 1
        """,
        (asset_id,)
    )