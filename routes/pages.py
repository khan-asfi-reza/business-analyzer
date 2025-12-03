from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import HTMLResponse

from routes.base import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Landing page with the search bar"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/documentation", response_class=HTMLResponse)
async def documentation(request: Request):
    """Documentation page"""
    return templates.TemplateResponse("documentation.html", {"request": request})


@router.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    """Privacy policy page"""
    return templates.TemplateResponse("privacy.html", {"request": request})


@router.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    """Terms of service page"""
    return templates.TemplateResponse("terms.html", {"request": request})


@router.get("/support", response_class=HTMLResponse)
async def support(request: Request):
    """Support page"""
    return templates.TemplateResponse("support.html", {"request": request})
