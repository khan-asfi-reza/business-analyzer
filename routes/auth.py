
from fastapi import APIRouter, Request, Form, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import bcrypt

from db import get_db_dependency, fetch_one, execute, transaction

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Display login form"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db = Depends(get_db_dependency)
):
    """Handle login form submission"""
    user = fetch_one(
        db,
        "SELECT user_id, username, email, password_hash, full_name, role FROM user WHERE username = %s",
        (username,)
    )
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"}
        )

    if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"}
        )

    request.session["user"] = {
        "user_id": user["user_id"],
        "username": user["username"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"]
    }

    next_url = request.query_params.get("next", "/dashboard")
    return RedirectResponse(url=next_url, status_code=303)


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Display registration form"""
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    db = Depends(get_db_dependency)
):
    """Handle registration form submission"""
    existing_user = fetch_one(
        db,
        "SELECT user_id FROM user WHERE email = %s",
        (email,)
    )

    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Email already registered"}
        )

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    with transaction(db):
        execute(
            db,
            """
            INSERT INTO user (username, email, password_hash, full_name, role)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (username, email, password_hash, full_name, 'Customer')
        )

    return RedirectResponse(url="/auth/login?registered=true", status_code=303)


@router.post("/logout")
async def logout(request: Request):
    """Handle logout - clear session"""
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@router.get("/logout")
async def logout_get(request: Request):
    """Handle logout GET request - clear session"""
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@router.get("/admin/secret/create", response_class=HTMLResponse)
async def admin_create_page(request: Request):
    """Display admin creation form for development"""
    return templates.TemplateResponse("admin_create_secret.html", {"request": request})


@router.post("/admin/secret/create")
async def admin_create_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    db = Depends(get_db_dependency)
):
    """Handle admin creation form submission"""
    existing_user = fetch_one(
        db,
        "SELECT user_id FROM user WHERE email = %s",
        (email,)
    )

    if existing_user:
        return templates.TemplateResponse(
            "admin_create_secret.html",
            {"request": request, "error": "Email already registered"}
        )

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    with transaction(db):
        execute(
            db,
            """
            INSERT INTO user (username, email, password_hash, full_name, role)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (username, email, password_hash, full_name, 'Admin')
        )

    return templates.TemplateResponse(
        "admin_create_secret.html",
        {"request": request, "success": f"Admin user '{username}' created successfully! You can now login."}
    )