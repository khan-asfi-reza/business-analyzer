from typing import Any

import bcrypt
from fastapi import Depends, Form, APIRouter
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from tasks.stock_data import fetch_stock_prices
from tasks.recommendations import update_single_company
from db import get_db_dependency, fetch_one, fetch_all, transaction, execute
from routes.base import templates, get_auth_user

router = APIRouter()

@router.get("", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db = Depends(get_db_dependency), user = Depends(get_auth_user)):
    """Admin dashboard overview page"""
    if isinstance(user, RedirectResponse):
        return user
    

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    stats = {}
    try:
        from db import fetch_one
        stats['total_users'] = fetch_one(db, "SELECT COUNT(*) as count FROM user", ())['count']
        stats['total_companies'] = fetch_one(db, "SELECT COUNT(*) as count FROM company", ())['count']
        stats['total_assets'] = fetch_one(db, "SELECT COUNT(*) as count FROM asset", ())['count']
        stats['total_content'] = fetch_one(db, "SELECT COUNT(*) as count FROM scraped_content", ())['count']
    except Exception as e:
        print(f"Error fetching stats: {e}")
        stats = {'total_users': 0, 'total_companies': 0, 'total_assets': 0, 'total_content': 0}

    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "user": user, "stats": stats}
    )


@router.get("/users", response_class=HTMLResponse,)
async def admin_users(
    request: Request,
    db = Depends(get_db_dependency), 
    user = Depends(get_auth_user),
    q: str = "",
    role: str = "",
    sort: str = "registration_date_desc",
    page: int = 1
):
    """Admin users page - list all users with q, filtering, sorting, and pagination"""
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    per_page = 20
    offset = (page - 1) * per_page

    where_clauses = []
    params = []

    if q:
        where_clauses.append("(user_id = %s OR username LIKE %s OR email LIKE %s OR full_name LIKE %s)")
        try:
            q_id = int(q)
            params.extend([q_id, f"%{q}%", f"%{q}%", f"%{q}%"])
        except ValueError:
            params.extend([0, f"%{q}%", f"%{q}%", f"%{q}%"])

    if role:
        where_clauses.append("role = %s")
        params.append(role)

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    valid_sorts = {
        "user_id_asc": ("user_id", "ASC"),
        "user_id_desc": ("user_id", "DESC"),
        "username_asc": ("username", "ASC"),
        "username_desc": ("username", "DESC"),
        "email_asc": ("email", "ASC"),
        "email_desc": ("email", "DESC"),
        "full_name_asc": ("full_name", "ASC"),
        "full_name_desc": ("full_name", "DESC"),
        "role_asc": ("role", "ASC"),
        "role_desc": ("role", "DESC"),
        "registration_date_asc": ("registration_date", "ASC"),
        "registration_date_desc": ("registration_date", "DESC"),
    }

    sort_by, sort_order = valid_sorts.get(sort, ("registration_date", "DESC"))

    count_query = f"SELECT COUNT(*) as count FROM user {where_sql}"
    total_users = fetch_one(db, count_query, tuple(params))['count']
    total_pages = (total_users + per_page - 1) // per_page

    query = f"""
        SELECT
            user_id, username, email, full_name,
            role, registration_date
        FROM user
        {where_sql}
        ORDER BY {sort_by} {sort_order}
        LIMIT %s OFFSET %s
    """
    params.extend([per_page, offset])
    users = fetch_all(db, query, tuple(params))

    return templates.TemplateResponse(
        "admin_users.html",
        {
            "request": request,
            "user": user,
            "users": users,
            "q": q,
            "role_filter": role,
            "sort": sort,
            "page": page,
            "total_pages": total_pages,
            "total_users": total_users
        }
    )


@router.get("/companies", response_class=HTMLResponse)
async def admin_companies(
    request: Request,
    db = Depends(get_db_dependency), 
    user = Depends(get_auth_user),
    q: str = "",
    company_type: str = "",
    industry: str = "",
    sort: str = "company_name_asc",
    page: int = 1
):
    """Admin companies page - list all companies with search, filtering, sorting, and pagination"""
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    per_page = 20
    offset = (page - 1) * per_page

    where_clauses = []
    params = []

    if q:
        where_clauses.append("(company_id = %s OR company_name LIKE %s OR industry LIKE %s)")
        try:
            search_id = int(q)
            params.extend([search_id, f"%{q}%", f"%{q}%"])
        except ValueError:
            params.extend([0, f"%{q}%", f"%{q}%"])

    if company_type:
        where_clauses.append("company_type = %s")
        params.append(company_type)

    if industry:
        where_clauses.append("industry = %s")
        params.append(industry)

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # Parse sort parameter (format: field_direction)
    valid_sorts = {
        "company_id_asc": ("company_id", "ASC"),
        "company_id_desc": ("company_id", "DESC"),
        "company_name_asc": ("company_name", "ASC"),
        "company_name_desc": ("company_name", "DESC"),
        "company_type_asc": ("company_type", "ASC"),
        "company_type_desc": ("company_type", "DESC"),
        "industry_asc": ("industry", "ASC"),
        "industry_desc": ("industry", "DESC"),
        "market_cap_asc": ("market_cap", "ASC"),
        "market_cap_desc": ("market_cap", "DESC"),
        "founded_date_asc": ("founded_date", "ASC"),
        "founded_date_desc": ("founded_date", "DESC"),
    }

    sort_by, sort_order = valid_sorts.get(sort, ("company_name", "ASC"))

    # Get total count
    count_query = f"SELECT COUNT(*) as count FROM company {where_sql}"
    total_companies = fetch_one(db, count_query, tuple(params))['count']
    total_pages = (total_companies + per_page - 1) // per_page

    # Get companies with pagination
    query = f"""
        SELECT
            company_id, company_name, company_type, industry,
            market_cap, founded_date, logo_url, stock_symbol, stock_exchange
        FROM company
        {where_sql}
        ORDER BY {sort_by} {sort_order}
        LIMIT %s OFFSET %s
    """
    params.extend([per_page, offset])
    companies = fetch_all(db, query, tuple(params))

    # Get distinct industries for filter dropdown
    industries = fetch_all(db, "SELECT DISTINCT industry FROM company WHERE industry IS NOT NULL ORDER BY industry", ())

    return templates.TemplateResponse(
        "admin_companies.html",
        {
            "request": request,
            "user": user,
            "companies": companies,
            "q": q,
            "company_type_filter": company_type,
            "industry_filter": industry,
            "sort": sort,
            "page": page,
            "total_pages": total_pages,
            "total_companies": total_companies,
            "industries": industries
        }
    )


@router.get("/assets", response_class=HTMLResponse)
async def admin_assets(
    request: Request,
    db = Depends(get_db_dependency), 
    user = Depends(get_auth_user),
    q: str = "",
    asset_type: str = "",
    sort: str = "asset_name_asc",
    page: int = 1
):
    """Admin assets page - list all assets with search, filtering, sorting, and pagination"""
    
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    per_page = 20
    offset = (page - 1) * per_page
    where_clauses = []
    params = []

    if q:
        where_clauses.append("(asset_id = %s OR asset_name LIKE %s OR asset_type LIKE %s)")
        try:
            search_id = int(q)
            params.extend([search_id, f"%{q}%", f"%{q}%"])
        except ValueError:
            params.extend([0, f"%{q}%", f"%{q}%"])

    if asset_type:
        where_clauses.append("asset_type = %s")
        params.append(asset_type)

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    valid_sorts = {
        "asset_id_asc": ("asset_id", "ASC"),
        "asset_id_desc": ("asset_id", "DESC"),
        "asset_name_asc": ("asset_name", "ASC"),
        "asset_name_desc": ("asset_name", "DESC"),
        "asset_type_asc": ("asset_type", "ASC"),
        "asset_type_desc": ("asset_type", "DESC"),
        "unit_of_measurement_asc": ("unit_of_measurement", "ASC"),
        "unit_of_measurement_desc": ("unit_of_measurement", "DESC"),
    }

    sort_by, sort_order = valid_sorts.get(sort, ("asset_name", "ASC"))

    count_query = f"SELECT COUNT(*) as count FROM asset {where_sql}"
    total_assets = fetch_one(db, count_query, tuple(params))['count']
    total_pages = (total_assets + per_page - 1) // per_page

    query = f"""
        SELECT
            asset_id, asset_name, asset_type,
            unit_of_measurement, description, logo_url
        FROM asset
        {where_sql}
        ORDER BY {sort_by} {sort_order}
        LIMIT %s OFFSET %s
    """
    params.extend([per_page, offset])
    assets = fetch_all(db, query, tuple(params))

    asset_types = fetch_all(db, "SELECT DISTINCT asset_type FROM asset WHERE asset_type <> '' ORDER BY asset_type", ())

    return templates.TemplateResponse(
        "admin_assets.html",
        {
            "request": request,
            "user": user,
            "assets": assets,
            "q": q,
            "asset_type_filter": asset_type,
            "sort": sort,
            "page": page,
            "total_pages": total_pages,
            "total_assets": total_assets,
            "asset_types": asset_types
        }
    )


@router.get("/content", response_class=HTMLResponse)
async def admin_content(request: Request, db = Depends(get_db_dependency), user = Depends(get_auth_user)):
    """Admin content page - list all scraped content"""
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    content_items = fetch_all(
        db,
        """
        SELECT
            sc.content_id, sc.title, sc.source_name, sc.content_type,
            sc.author, sc.publish_date, sc.scraped_date, sc.source_url,
            sa.sentiment_label, sa.sentiment_score, sa.confidence_level
        FROM scraped_content sc
        LEFT JOIN sentiment_analysis sa ON sc.content_id = sa.content_id
        ORDER BY sc.scraped_date DESC
        LIMIT 100
        """,
        ()
    )

    return templates.TemplateResponse(
        "admin_content.html",
        {"request": request, "user": user, "content_items": content_items}
    )


@router.get("/users/add", response_class=HTMLResponse)
async def admin_user_add_form(request: Request, user=Depends(get_auth_user)):
    """Show add user form"""
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    return templates.TemplateResponse(
        "admin_user_form.html",
        {"request": request, "user": user, "form_user": None, "mode": "add"}
    )


@router.post("/users/add")
async def admin_user_add_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    user=Depends(get_auth_user),
    db = Depends(get_db_dependency)
):
    """Handle add user form submission"""
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    # Check if username or email already exists
    existing = fetch_one(db, "SELECT user_id FROM user WHERE username = %s OR email = %s", (username, email))
    if existing:
        return templates.TemplateResponse(
            "admin_user_form.html",
            {"request": request, "user": user, "form_user": None, "mode": "add", "error": "Username or email already exists"}
        )

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Insert user
    with transaction(db):
        execute(
            db,
            "INSERT INTO user (username, email, password_hash, full_name, role) VALUES (%s, %s, %s, %s, %s)",
            (username, email, password_hash, full_name, role)
        )

    return RedirectResponse(url="/admin/users?success=User added successfully", status_code=303)


@router.get("/users/edit/{user_id}", response_class=HTMLResponse)
async def admin_user_edit_form(request: Request, user_id: int, db = Depends(get_db_dependency), user = Depends(get_auth_user)):
    """Show edit user form"""
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    form_user = fetch_one(db, "SELECT user_id, username, email, full_name, role FROM user WHERE user_id = %s", (user_id,))
    if not form_user:
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=404)

    return templates.TemplateResponse(
        "admin_user_form.html",
        {"request": request, "user": user, "form_user": form_user, "mode": "edit"}
    )


@router.post("/users/edit/{user_id}")
async def admin_user_edit_submit(
    request: Request,
    user_id: int,
    username: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(None),
    role: str = Form(...),
    db = Depends(get_db_dependency),
    user=Depends(get_auth_user),
):
    """Handle edit user form submission"""
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    existing = fetch_one(
        db,
        "SELECT user_id FROM user WHERE (username = %s OR email = %s) AND user_id != %s",
        (username, email, user_id)
    )
    if existing:
        form_user = fetch_one(db, "SELECT user_id, username, email, full_name, role FROM user WHERE user_id = %s", (user_id,))
        return templates.TemplateResponse(
            "admin_user_form.html",
            {"request": request, "user": user, "form_user": form_user, "mode": "edit", "error": "Username or email already exists"}
        )

    # Update user
    with transaction(db):
        if password:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            execute(
                db,
                "UPDATE user SET username = %s, email = %s, full_name = %s, password_hash = %s, role = %s WHERE user_id = %s",
                (username, email, full_name, password_hash, role, user_id)
            )
        else:
            execute(
                db,
                "UPDATE user SET username = %s, email = %s, full_name = %s, role = %s WHERE user_id = %s",
                (username, email, full_name, role, user_id)
            )

    return RedirectResponse(url="/admin/users?success=User updated successfully", status_code=303)


@router.get("/companies/add", response_class=HTMLResponse)
async def admin_company_add_form(request: Request, user=Depends(get_auth_user)):
    """Show add company form"""
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    return templates.TemplateResponse(
        "admin_company_form.html",
        {"request": request, "user": user, "company": None, "mode": "add"}
    )


@router.post("/companies/add")
async def admin_company_add_submit(
    request: Request,
    company_name: str = Form(...),
    company_type: str = Form(...),
    industry: str = Form(...),
    logo_url: str = Form(None),
    founded_date: str = Form(None),
    description: str = Form(None),
    market_cap: float = Form(None),
    stock_symbol: str = Form(None),
    stock_exchange: str = Form(None),
    db = Depends(get_db_dependency),
    user=Depends(get_auth_user),
):
    """Handle add company form submission"""
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    with transaction(db):
        execute(
            db,
            """INSERT INTO company (company_name, company_type, industry, logo_url, founded_date, description, market_cap, stock_symbol, stock_exchange)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (company_name, company_type, industry, logo_url or None, founded_date or None, description or None, market_cap, stock_symbol or None, stock_exchange or None)
        )

    return RedirectResponse(url="/admin/companies?success=Company added successfully", status_code=303)


@router.get("/companies/edit/{company_id}", response_class=HTMLResponse)
async def admin_company_edit_form(request: Request, company_id: int, db = Depends(get_db_dependency), user = Depends(get_auth_user)):
    """Show edit company form"""
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    company = fetch_one(
        db,
        "SELECT company_id, company_name, company_type, industry, logo_url, founded_date, description, market_cap, stock_symbol, stock_exchange FROM company WHERE company_id = %s",
        (company_id,)
    )
    if not company:
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=404)

    return templates.TemplateResponse(
        "admin_company_form.html",
        {"request": request, "user": user, "company": company, "mode": "edit"}
    )


@router.post("/companies/edit/{company_id}")
async def admin_company_edit_submit(
    request: Request,
    company_id: int,
    company_name: str = Form(...),
    company_type: str = Form(...),
    industry: str = Form(...),
    logo_url: str = Form(None),
    founded_date: str = Form(None),
    description: str = Form(None),
    market_cap: float = Form(None),
    stock_symbol: str = Form(None),
    stock_exchange: str = Form(None),
    db = Depends(get_db_dependency),
    user=Depends(get_auth_user),
):
    """Handle edit company form submission"""
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    with transaction(db):
        execute(
            db,
            """UPDATE company SET company_name = %s, company_type = %s, industry = %s, logo_url = %s,
               founded_date = %s, description = %s, market_cap = %s, stock_symbol = %s, stock_exchange = %s WHERE company_id = %s""",
            (company_name, company_type, industry, logo_url or None, founded_date or None, description or None, market_cap, stock_symbol or None, stock_exchange or None, company_id)
        )

    return RedirectResponse(url="/admin/companies?success=Company updated successfully", status_code=303)


@router.get("/assets/add", response_class=HTMLResponse)
async def admin_asset_add_form(request: Request, user=Depends(get_auth_user),):
    """Show add asset form"""
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    return templates.TemplateResponse(
        "admin_asset_form.html",
        {"request": request, "user": user, "asset": None, "mode": "add"}
    )


@router.post("/assets/add")
async def admin_asset_add_submit(
    request: Request,
    asset_name: str = Form(...),
    asset_type: str = Form(...),
    unit_of_measurement: str = Form(...),
    logo_url: str = Form(None),
    description: str = Form(None),
    db = Depends(get_db_dependency),
    user=Depends(get_auth_user),
):
    """Handle add asset form submission"""
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    with transaction(db):
        execute(
            db,
            """INSERT INTO asset (asset_name, asset_type, unit_of_measurement, logo_url, description)
               VALUES (%s, %s, %s, %s, %s)""",
            (asset_name, asset_type, unit_of_measurement, logo_url or None, description or None)
        )

    return RedirectResponse(url="/admin/assets?success=Asset added successfully", status_code=303)


@router.get("/assets/edit/{asset_id}", response_class=HTMLResponse)
async def admin_asset_edit_form(request: Request, asset_id: int, db = Depends(get_db_dependency), user = Depends(get_auth_user)):
    """Show edit asset form"""
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    asset = fetch_one(
        db,
        "SELECT asset_id, asset_name, asset_type, unit_of_measurement, logo_url, description FROM asset WHERE asset_id = %s",
        (asset_id,)
    )
    if not asset:
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=404)

    return templates.TemplateResponse(
        "admin_asset_form.html",
        {"request": request, "user": user, "asset": asset, "mode": "edit"}
    )


@router.post("/assets/edit/{asset_id}")
async def admin_asset_edit_submit(
    request: Request,
    asset_id: int,
    asset_name: str = Form(...),
    asset_type: str = Form(...),
    unit_of_measurement: str = Form(...),
    logo_url: str = Form(None),
    description: str = Form(None),
    db = Depends(get_db_dependency),
    user=Depends(get_auth_user),
):
    """Handle edit asset form submission"""
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    with transaction(db):
        execute(
            db,
            """UPDATE asset SET asset_name = %s, asset_type = %s, unit_of_measurement = %s, logo_url = %s, description = %s
               WHERE asset_id = %s""",
            (asset_name, asset_type, unit_of_measurement, logo_url or None, description or None, asset_id)
        )

    return RedirectResponse(url="/admin/assets?success=Asset updated successfully", status_code=303)


@router.get("/companies/{company_id}/detail", response_class=HTMLResponse)
async def admin_company_detail(
    request: Request,
    company_id: int,
    db = Depends(get_db_dependency),
    user = Depends(get_auth_user),
    date_from: str = "",
    date_to: str = ""
):
    """
    Shows company detail page with recommendations and news
    """
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=403)

    company = fetch_one(
        db,
        "SELECT company_id, company_name, company_type, industry, logo_url, founded_date, description, market_cap, stock_symbol, stock_exchange FROM company WHERE company_id = %s",
        (company_id,)
    )

    if not company:
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=404)

    where_clauses = []
    params: list[Any] = [company_id]

    if date_from:
        where_clauses.append("recommendation_date >= %s")
        params.append(date_from)

    if date_to:
        where_clauses.append("recommendation_date <= %s")
        params.append(date_to)

    where_sql = "AND " + " AND ".join(where_clauses) if where_clauses else ""

    recommendations = fetch_all(
        db,
        f"""
        SELECT recommendation_id, recommendation_type, investment_score, risk_level,
               expected_return, rationale_summary, recommendation_date
        FROM investment_recommendation
        WHERE company_id = %s {where_sql}
        ORDER BY recommendation_date DESC LIMIT 50
        """,
        tuple(params)
    )

    news_items = fetch_all(
        db,
        """
        SELECT sc.content_id, sc.title, sc.source_name, sc.publish_date, sc.source_url,
               SUBSTRING(sc.content_text, 1, 200) as excerpt,
               sa.sentiment_label, sa.sentiment_score
        FROM scraped_content sc
        LEFT JOIN sentiment_analysis sa ON sc.content_id = sa.content_id
        WHERE sc.company_id = %s
        ORDER BY sc.publish_date DESC
        LIMIT 50
        """,
        (company_id,)
    )

    return templates.TemplateResponse(
        "admin_company_detail.html",
        {
            "request": request,
            "user": user,
            "company": company,
            "recommendations": recommendations,
            "news_items": news_items,
            "date_from": date_from,
            "date_to": date_to
        }
    )


@router.post("/companies/{company_id}/fetch-prices")
async def admin_company_fetch_prices(
    request: Request,
    company_id: int,
    db = Depends(get_db_dependency),
    user = Depends(get_auth_user)
):
    """
    Fetches stock prices for a company using its database stock_symbol
    """
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return RedirectResponse(url="/admin", status_code=303)

    company = fetch_one(db, "SELECT stock_symbol, stock_exchange FROM company WHERE company_id = %s", (company_id,))

    if not company or not company.get('stock_symbol'):
        return RedirectResponse(
            url=f"/admin/companies/{company_id}/detail?error=Stock symbol not set for this company",
            status_code=303
        )



    ticker_symbol = company['stock_symbol']
    print(ticker_symbol)
    print(fetch_stock_prices.apply_async(
        kwargs=dict(
            company_id=company_id,
            ticker_symbol=ticker_symbol,
            days=60,
        )
    ))


    return RedirectResponse(
        url=f"/admin/companies/{company_id}/detail?success=Stock prices fetch started for {ticker_symbol}",
        status_code=303
    )


@router.post("/companies/{company_id}/run-recommendation")
async def admin_company_run_recommendation(
    request: Request,
    company_id: int,
    db = Depends(get_db_dependency),
    user = Depends(get_auth_user)
):
    """
    Runs AI-powered recommendation generation for a company
    """
    if isinstance(user, RedirectResponse):
        return user

    if user.get("role") != "Admin":
        return RedirectResponse(url="/admin", status_code=303)

    update_single_company.apply_async(kwargs=dict(company_id=company_id))

    return RedirectResponse(
        url=f"/admin/companies/{company_id}/detail?success=Recommendation generation started",
        status_code=303
    )
