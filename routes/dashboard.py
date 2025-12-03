from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from db import get_db_dependency, fetch_all
from routes.base import templates, get_auth_user

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """User dashboard with summary and recent recommendations"""
    user = get_auth_user(request)
    context = {
        "request": request,
        "user": user,
        "user_name": user.get("full_name", user.get("username")),
        "companies_count": 0,
        "assets_count": 0,
        "recent_recommendations": []
    }
    return templates.TemplateResponse("dashboard.html", context)


@router.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = "", db = Depends(get_db_dependency)):
    """Search results for companies and assets"""
    user = get_auth_user(request)
    results = []
    if q:
        companies = fetch_all(
            db,
            """
            SELECT company_id, company_name, 'company' as type, industry
            FROM company
            WHERE company_name LIKE %s OR industry LIKE %s
            LIMIT 20
            """,
            (f"%{q}%", f"%{q}%")
        )
        assets = fetch_all(
            db,
            """
            SELECT asset_id, asset_name, 'asset' as type, asset_type
            FROM asset
            WHERE asset_name LIKE %s OR asset_type LIKE %s
            LIMIT 20
            """,
            (f"%{q}%", f"%{q}%")
        )
        results = companies + assets

    return templates.TemplateResponse(
        "search.html",
        {"request": request, "user": user, "query": q, "results": results}
    )


@router.get("/company/{company_id}", response_class=HTMLResponse)
async def company_detail(request: Request, company_id: int):
    """Company detail page"""
    user = get_auth_user(request)

    context = {
        "request": request,
        "user": user,
        "company": {},
    }

    return templates.TemplateResponse("company_detail.html", context)


@router.get("/asset/{asset_id}", response_class=HTMLResponse)
async def asset_detail(request: Request, asset_id: int):
    """Asset detail page"""
    user = get_auth_user(request)

    context = {
        "request": request,
        "user": user,
        "asset": {},
    }

    return templates.TemplateResponse("asset_detail.html", context)


@router.get("/watchlist", response_class=HTMLResponse)
async def watchlist(request: Request):
    """User's bookmarked items"""
    user = get_auth_user(request)

    context = {
        "request": request,
        "user": user,
        "bookmarks": []
    }

    return templates.TemplateResponse("watchlist.html", context)


@router.get("/news", response_class=HTMLResponse)
async def news(request: Request, db = Depends(get_db_dependency)):
    """Scraped content with sentiment"""
    user = get_auth_user(request)

    news_items = fetch_all(
        db,
        """
        SELECT
            sc.content_id, sc.title, sc.source_name, sc.content_type,
            sc.publish_date, sc.scraped_date, sc.source_url,
            SUBSTRING(sc.content_text, 1, 200) as excerpt,
            sa.sentiment_label, sa.sentiment_score, sa.confidence_level
        FROM scraped_content sc
        LEFT JOIN sentiment_analysis sa ON sc.content_id = sa.content_id
        ORDER BY sc.publish_date DESC
        LIMIT 50
        """,
        ()
    )

    return templates.TemplateResponse(
        "news.html",
        {"request": request, "user": user, "news_items": news_items}
    )


