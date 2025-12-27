from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Form
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from db import get_db_dependency, fetch_all, fetch_one, execute, transaction
from routes.base import get_auth_user
from services.chatbot_service import (
    get_company_context,
    save_chat_message,
    get_chat_history,
    create_session_id
)
from ai import answer_company_question

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
async def add_bookmark(
    company_id: Optional[int] = Form(None),
    asset_id: Optional[int] = Form(None),
    notes: Optional[str] = Form(None),
    db = Depends(get_db_dependency),
    user = Depends(get_auth_user)
):
    """Add company or asset to user's watchlist"""
    if isinstance(user, RedirectResponse):
        return user

    user_id = user.get("user_id")

    if not company_id and not asset_id:
        raise HTTPException(status_code=400, detail="Must provide either company_id or asset_id")

    if company_id:
        existing = fetch_one(
            db,
            "SELECT bookmark_id FROM bookmark WHERE user_id = %s AND company_id = %s",
            (user_id, company_id)
        )
    else:
        existing = fetch_one(
            db,
            "SELECT bookmark_id FROM bookmark WHERE user_id = %s AND asset_id = %s",
            (user_id, asset_id)
        )

    if existing:
        return RedirectResponse(url="/dashboard/watchlist?msg=already_added", status_code=303)

    with transaction(db):
        bookmark_id = execute(
            db,
            """
            INSERT INTO bookmark (user_id, company_id, asset_id, notes)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, company_id, asset_id, notes)
        )

    return RedirectResponse(url="/dashboard/watchlist?msg=added", status_code=303)


@router.post("/bookmark/remove")
async def remove_bookmark(
    bookmark_id: int = Form(...),
    db = Depends(get_db_dependency),
    user = Depends(get_auth_user)
):
    """Remove bookmark from user's watchlist"""
    if isinstance(user, RedirectResponse):
        return user

    user_id = user.get("user_id")

    with transaction(db):
        rows_affected = execute(
            db,
            "DELETE FROM bookmark WHERE bookmark_id = %s AND user_id = %s",
            (bookmark_id, user_id)
        )

    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    return RedirectResponse(url="/dashboard/watchlist", status_code=303)


@router.post("/bookmark/update-notes")
async def update_bookmark_notes(
    company_id: Optional[int] = Form(None),
    asset_id: Optional[int] = Form(None),
    notes: str = Form(...),
    db = Depends(get_db_dependency),
    user = Depends(get_auth_user)
):
    """Update notes for a bookmark"""
    if isinstance(user, RedirectResponse):
        return user

    user_id = user.get("user_id")

    if not company_id and not asset_id:
        raise HTTPException(status_code=400, detail="Must provide either company_id or asset_id")

    if company_id:
        bookmark = fetch_one(
            db,
            "SELECT bookmark_id FROM bookmark WHERE user_id = %s AND company_id = %s",
            (user_id, company_id)
        )
    else:
        bookmark = fetch_one(
            db,
            "SELECT bookmark_id FROM bookmark WHERE user_id = %s AND asset_id = %s",
            (user_id, asset_id)
        )

    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found. Please add to watchlist first.")

    # Update notes
    with transaction(db):
        execute(
            db,
            "UPDATE bookmark SET notes = %s WHERE bookmark_id = %s",
            (notes, bookmark["bookmark_id"])
        )

    return {"success": True, "message": "Notes updated successfully"}


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@router.post("/company/{company_id}/chat")
async def chat_with_company(
    company_id: int,
    chat_request: ChatRequest,
    db = Depends(get_db_dependency),
    user = Depends(get_auth_user)
):
    """Send a message to the AI chatbot about a company"""
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail="Authentication required")

    user_id = user.get("user_id")

    company_context = get_company_context(db, company_id)
    if not company_context:
        raise HTTPException(status_code=404, detail="Company not found")

    session_id = chat_request.session_id or create_session_id()

    with transaction(db):
        save_chat_message(
            db,
            user_id=user_id,
            company_id=company_id,
            session_id=session_id,
            message_text=chat_request.message,
            is_user_message=True
        )

    ai_response = answer_company_question(
        company_context=company_context,
        user_question=chat_request.message
    )

    if ai_response.get("error"):
        raise HTTPException(status_code=500, detail=ai_response["error"])

    answer = ai_response["answer"]

    with transaction(db):
        save_chat_message(
            db,
            user_id=user_id,
            company_id=company_id,
            session_id=session_id,
            message_text=answer,
            is_user_message=False
        )

    return {
        "answer": answer,
        "session_id": session_id
    }


@router.get("/company/{company_id}/chat/history")
async def get_company_chat_history(
    company_id: int,
    session_id: Optional[str] = None,
    limit: int = 50,
    db = Depends(get_db_dependency),
    user = Depends(get_auth_user)
):
    """Get chat history for a company"""
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail="Authentication required")

    user_id = user.get("user_id")

    history = get_chat_history(
        db,
        user_id=user_id,
        company_id=company_id,
        session_id=session_id,
        limit=limit
    )

    return {"history": history}