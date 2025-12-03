"""
Watchlist service - Bookmark management business logic
"""
from typing import List, Dict, Any

from db import fetch_all, execute, transaction


def get_user_bookmarks(db, user_id: int) -> List[Dict[str, Any]]:
    """Get all bookmarks for a user with company/asset details"""
    return fetch_all(
        db,
        """
        SELECT
            b.bookmark_id, b.bookmark_date, b.notes,
            c.company_id, c.company_name, c.industry,
            a.asset_id, a.asset_name, a.asset_type,
            CASE
                WHEN c.company_id IS NOT NULL THEN 'company'
                WHEN a.asset_id IS NOT NULL THEN 'asset'
            END as type
        FROM bookmark b
        LEFT JOIN company c ON b.company_id = c.company_id
        LEFT JOIN asset a ON b.asset_id = a.asset_id
        WHERE b.user_id = %s
        ORDER BY b.bookmark_date DESC
        """,
        (user_id,)
    )


def add_company_bookmark(db, user_id: int, company_id: int, notes: str = None) -> int:
    """Add a company to user's watchlist"""
    with transaction(db):
        bookmark_id = execute(
            db,
            """
            INSERT INTO bookmark (user_id, company_id, notes)
            VALUES (%s, %s, %s)
            """,
            (user_id, company_id, notes)
        )
    return bookmark_id


def add_asset_bookmark(db, user_id: int, asset_id: int, notes: str = None) -> int:
    """Add an asset to user's watchlist"""
    with transaction(db):
        bookmark_id = execute(
            db,
            """
            INSERT INTO bookmark (user_id, asset_id, notes)
            VALUES (%s, %s, %s)
            """,
            (user_id, asset_id, notes)
        )
    return bookmark_id


def remove_bookmark(db, user_id: int, bookmark_id: int) -> bool:
    """Remove a bookmark from user's watchlist"""
    with transaction(db):
        rows_affected = execute(
            db,
            "DELETE FROM bookmark WHERE bookmark_id = %s AND user_id = %s",
            (bookmark_id, user_id)
        )
    return rows_affected > 0


def update_bookmark_notes(db, user_id: int, bookmark_id: int, notes: str) -> bool:
    """Update notes for a bookmark"""
    with transaction(db):
        rows_affected = execute(
            db,
            "UPDATE bookmark SET notes = %s WHERE bookmark_id = %s AND user_id = %s",
            (notes, bookmark_id, user_id)
        )
    return rows_affected > 0


def get_bookmark_counts(db, user_id: int) -> Dict[str, int]:
    """Get count of company and asset bookmarks for a user"""
    result = fetch_all(
        db,
        """
        SELECT
            SUM(CASE WHEN company_id IS NOT NULL THEN 1 ELSE 0 END) as companies_count,
            SUM(CASE WHEN asset_id IS NOT NULL THEN 1 ELSE 0 END) as assets_count
        FROM bookmark
        WHERE user_id = %s
        """,
        (user_id,)
    )

    if result:
        return {
            "companies_count": result[0].get("companies_count", 0) or 0,
            "assets_count": result[0].get("assets_count", 0) or 0
        }

    return {"companies_count": 0, "assets_count": 0}