from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from db import get_db_dependency, fetch_all, fetch_one, execute, transaction

router = APIRouter()


class SearchResult(BaseModel):
    id: int
    name: str
    type: str
    details: Optional[str] = None


class PriceData(BaseModel):
    date: str
    price: float
    currency: str


class BookmarkRequest(BaseModel):
    company_id: Optional[int] = None
    asset_id: Optional[int] = None
    notes: Optional[str] = None


@router.get("/search")
async def api_search(q: str = "", db = Depends(get_db_dependency)):
    """Search API for companies and assets"""
    if not q:
        return {"results": []}

    companies = fetch_all(
        db,
        "SELECT company_id as id, company_name as name, 'company' as type, industry as details FROM company WHERE company_name LIKE %s LIMIT 20",
        (f"%{q}%",)
    )

    # Search assets
    assets = fetch_all(
        db,
        "SELECT asset_id as id, asset_name as name, 'asset' as type, asset_type as details FROM asset WHERE asset_name LIKE %s LIMIT 20",
        (f"%{q}%",)
    )

    results = companies + assets
    return {"results": results}


@router.get("/company/{company_id}/prices")
async def get_company_prices(company_id: int, limit: int = 30, db = Depends(get_db_dependency)):
    prices = fetch_all(
        db,
        """
        SELECT date, close_price as price, currency
        FROM stock_price
        WHERE company_id = %s
        ORDER BY date DESC
        LIMIT %s
        """,
        (company_id, limit)
    )

    if not prices:
        raise HTTPException(status_code=404, detail="Company not found or no price data")

    return {"company_id": company_id, "prices": prices}


@router.get("/asset/{asset_id}/prices")
async def get_asset_prices(asset_id: int, limit: int = 30, db = Depends(get_db_dependency)):
    """Get price history for an asset"""
    prices = fetch_all(
        db,
        """
        SELECT date, price, currency
        FROM asset_price
        WHERE asset_id = %s
        ORDER BY date DESC
        LIMIT %s
        """,
        (asset_id, limit)
    )
    if not prices:
        raise HTTPException(status_code=404, detail="Asset not found or no price data")

    return {"asset_id": asset_id, "prices": prices}


@router.get("/company/{company_id}/recommendation")
async def get_company_recommendation(company_id: int, db = Depends(get_db_dependency)):
    recommendation = fetch_one(
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

    if not recommendation:
        raise HTTPException(status_code=404, detail="No recommendation found")

    return recommendation


@router.post("/bookmark/add")
async def add_bookmark(bookmark: BookmarkRequest, db = Depends(get_db_dependency)):
    """Add company or asset to user's watchlist"""
    user_id = 1  # Placeholder

    if not bookmark.company_id and not bookmark.asset_id:
        raise HTTPException(status_code=400, detail="Must provide either company_id or asset_id")

    with transaction(db):
        bookmark_id = execute(
            db,
            """
            INSERT INTO bookmark (user_id, company_id, asset_id, notes)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, bookmark.company_id, bookmark.asset_id, bookmark.notes)
        )

    return {"bookmark_id": bookmark_id, "message": "Added to watchlist"}


@router.post("/bookmark/remove")
async def remove_bookmark(bookmark_id: int, db = Depends(get_db_dependency)):
    """Remove bookmark from user's watchlist"""
    user_id = 1  # Placeholder

    with transaction(db):
        rows_affected = execute(
            db,
            "DELETE FROM bookmark WHERE bookmark_id = %s AND user_id = %s",
            (bookmark_id, user_id)
        )

    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    return {"message": "Removed from watchlist"}