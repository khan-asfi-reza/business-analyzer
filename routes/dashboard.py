from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse

from db import get_db_dependency, fetch_all, fetch_one
from routes.base import templates, get_auth_user
from services.watchlist_service import get_bookmark_counts, get_user_bookmarks
from services.company_service import (
    get_company_by_id,
    get_latest_stock_price,
    get_stock_prices,
    get_latest_financial_statement,
    get_company_recommendation
)
from services.asset_service import (
    get_asset_by_id,
    get_latest_asset_price,
    get_asset_prices,
    get_asset_recommendation
)

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db = Depends(get_db_dependency), user = Depends(get_auth_user)):
    """User dashboard with summary and recent recommendations"""
    if isinstance(user, RedirectResponse):
        return user

    user_id = user.get("user_id")

    counts = get_bookmark_counts(db, user_id)

    recent_recommendations = fetch_all(
        db,
        """
        SELECT
            ir.recommendation_id,
            ir.recommendation_type,
            ir.investment_score,
            ir.risk_level,
            ir.recommendation_date,
            c.company_id,
            c.company_name,
            a.asset_id,
            a.asset_name,
            CASE
                WHEN c.company_id IS NOT NULL THEN 'company'
                WHEN a.asset_id IS NOT NULL THEN 'asset'
            END as type
        FROM investment_recommendation ir
        LEFT JOIN company c ON ir.company_id = c.company_id
        LEFT JOIN asset a ON ir.asset_id = a.asset_id
        ORDER BY ir.recommendation_date DESC
        LIMIT 10
        """,
        ()
    )

    context = {
        "request": request,
        "user": user,
        "user_name": user.get("full_name", user.get("username")),
        "companies_count": counts["companies_count"],
        "assets_count": counts["assets_count"],
        "recent_recommendations": recent_recommendations
    }
    return templates.TemplateResponse("dashboard.html", context)


@router.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = "", db = Depends(get_db_dependency), user = Depends(get_auth_user)):
    """Search results for companies and assets"""
    if isinstance(user, RedirectResponse):
        return user
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
async def company_detail(request: Request, company_id: int, db = Depends(get_db_dependency), user = Depends(get_auth_user)):
    """Company detail page"""
    if isinstance(user, RedirectResponse):
        return user
    user_id = user.get("user_id")

    company = get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    latest_price = get_latest_stock_price(db, company_id)
    price_history = get_stock_prices(db, company_id, days=180)

    if price_history:
        for price in price_history:
            if 'close_price' in price:
                price['close_price'] = float(price['close_price'])
            if 'open_price' in price:
                price['open_price'] = float(price['open_price'])
            if 'high_price' in price:
                price['high_price'] = float(price['high_price'])
            if 'low_price' in price:
                price['low_price'] = float(price['low_price'])

    financial_statement = get_latest_financial_statement(db, company_id)
    recommendation = get_company_recommendation(db, company_id)

    bookmark_data = fetch_one(
        db,
        "SELECT bookmark_id, notes FROM bookmark WHERE user_id = %s AND company_id = %s",
        (user_id, company_id)
    )
    is_bookmarked = bookmark_data is not None
    existing_notes = bookmark_data.get("notes", "") if bookmark_data else ""

    sentiment_data = fetch_all(
        db,
        """
        SELECT AVG(sa.sentiment_score) as avg_sentiment, AVG(sa.confidence_level) as avg_confidence
        FROM sentiment_analysis sa
        JOIN scraped_content sc ON sa.content_id = sc.content_id
        WHERE sc.company_id = %s AND sc.publish_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """,
        (company_id,)
    )

    sentiment = None
    if sentiment_data and sentiment_data[0].get("avg_sentiment") is not None:
        avg_sent = sentiment_data[0]["avg_sentiment"]
        sentiment_score_pct = (avg_sent + 1) * 50  # Convert -1..1 to 0..100
        sentiment = {
            "score": sentiment_score_pct,
            "label": "positive" if avg_sent > 0.2 else ("negative" if avg_sent < -0.2 else "neutral"),
            "confidence": sentiment_data[0]["avg_confidence"] * 100 if sentiment_data[0]["avg_confidence"] else 0
        }

    context = {
        "request": request,
        "user": user,
        "company": company,
        "latest_price": latest_price,
        "price_history": price_history,
        "financial_statement": financial_statement,
        "recommendation": recommendation,
        "sentiment": sentiment,
        "is_bookmarked": is_bookmarked,
        "existing_notes": existing_notes
    }

    return templates.TemplateResponse("company-detail.html", context)


@router.get("/asset/{asset_id}", response_class=HTMLResponse)
async def asset_detail(request: Request, asset_id: int, db = Depends(get_db_dependency), user = Depends(get_auth_user)):
    """Asset detail page"""
    if isinstance(user, RedirectResponse):
        return user
    user_id = user.get("user_id")

    asset = get_asset_by_id(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    latest_price = get_latest_asset_price(db, asset_id)
    price_history = get_asset_prices(db, asset_id, days=180)
    recommendation = get_asset_recommendation(db, asset_id)

    bookmark_data = fetch_one(
        db,
        "SELECT bookmark_id, notes FROM bookmark WHERE user_id = %s AND asset_id = %s",
        (user_id, asset_id)
    )
    is_bookmarked = bookmark_data is not None
    existing_notes = bookmark_data.get("notes", "") if bookmark_data else ""

    sentiment = None

    context = {
        "request": request,
        "user": user,
        "asset": asset,
        "latest_price": latest_price,
        "price_history": price_history,
        "recommendation": recommendation,
        "sentiment": sentiment,
        "is_bookmarked": is_bookmarked,
        "existing_notes": existing_notes
    }

    return templates.TemplateResponse("asset-detail.html", context)


@router.get("/watchlist", response_class=HTMLResponse)
async def watchlist(request: Request, db = Depends(get_db_dependency), user = Depends(get_auth_user)):
    """User's bookmarked items"""
    if isinstance(user, RedirectResponse):
        return user
    user_id = user.get("user_id")

    bookmarks = get_user_bookmarks(db, user_id)

    for bookmark in bookmarks:
        if bookmark.get("company_id"):
            # Get recommendation
            rec = fetch_all(
                db,
                """
                SELECT recommendation_type, investment_score, risk_level
                FROM investment_recommendation
                WHERE company_id = %s
                ORDER BY recommendation_date DESC
                LIMIT 1
                """,
                (bookmark["company_id"],)
            )
            bookmark["recommendation"] = rec[0] if rec else None

            prices = fetch_all(
                db,
                """
                SELECT close_price, date
                FROM stock_price
                WHERE company_id = %s
                ORDER BY date DESC
                LIMIT 2
                """,
                (bookmark["company_id"],)
            )
            if prices and len(prices) > 0:
                bookmark["current_price"] = float(prices[0]["close_price"])
                if len(prices) > 1:
                    prev_price = float(prices[1]["close_price"])
                    bookmark["price_change"] = ((bookmark["current_price"] - prev_price) / prev_price) * 100
                else:
                    bookmark["price_change"] = 0
            else:
                bookmark["current_price"] = None
                bookmark["price_change"] = 0

        elif bookmark.get("asset_id"):
            rec = fetch_all(
                db,
                """
                SELECT recommendation_type, investment_score, risk_level
                FROM investment_recommendation
                WHERE asset_id = %s
                ORDER BY recommendation_date DESC
                LIMIT 1
                """,
                (bookmark["asset_id"],)
            )
            bookmark["recommendation"] = rec[0] if rec else None

            prices = fetch_all(
                db,
                """
                SELECT price, date
                FROM asset_price
                WHERE asset_id = %s
                ORDER BY date DESC
                LIMIT 2
                """,
                (bookmark["asset_id"],)
            )
            if prices and len(prices) > 0:
                bookmark["current_price"] = float(prices[0]["price"])
                if len(prices) > 1:
                    prev_price = float(prices[1]["price"])
                    bookmark["price_change"] = ((bookmark["current_price"] - prev_price) / prev_price) * 100
                else:
                    bookmark["price_change"] = 0
            else:
                bookmark["current_price"] = None
                bookmark["price_change"] = 0

    context = {
        "request": request,
        "user": user,
        "bookmarks": bookmarks
    }

    return templates.TemplateResponse("watchlist.html", context)


@router.get("/news", response_class=HTMLResponse)
async def news(
    request: Request,
    sentiment: str = "",
    page: int = 1,
    db = Depends(get_db_dependency),
    user = Depends(get_auth_user)
):
    """Scraped content with sentiment, filtering and pagination"""

    if isinstance(user, RedirectResponse):
        return user

    per_page = 10
    offset = (page - 1) * per_page

    where_clauses = []
    params = []

    if sentiment and sentiment != "all":
        where_clauses.append("sa.sentiment_label = %s")
        params.append(sentiment)

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    count_query = f"""
        SELECT COUNT(*) as count
        FROM scraped_content sc
        LEFT JOIN sentiment_analysis sa ON sc.content_id = sa.content_id
        {where_sql}
    """
    total_items = fetch_one(db, count_query, tuple(params))['count']
    total_pages = (total_items + per_page - 1) // per_page
    has_more = page < total_pages

    query = f"""
        SELECT
            sc.content_id, sc.title, sc.source_name, sc.content_type,
            sc.publish_date, sc.scraped_date, sc.source_url,
            SUBSTRING(sc.content_text, 1, 200) as excerpt,
            sa.sentiment_label, sa.sentiment_score, sa.confidence_level
        FROM scraped_content sc
        LEFT JOIN sentiment_analysis sa ON sc.content_id = sa.content_id
        {where_sql}
        ORDER BY sc.publish_date DESC
        LIMIT %s OFFSET %s
    """
    params.extend([per_page, offset])
    news_items = fetch_all(db, query, tuple(params))

    return templates.TemplateResponse(
        "news.html",
        {
            "request": request,
            "user": user,
            "news_items": news_items,
            "sentiment_filter": sentiment,
            "page": page,
            "total_pages": total_pages,
            "has_more": has_more
        }
    )


