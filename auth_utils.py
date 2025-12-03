"""
Authentication utilities for session management and auth dependencies
"""
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse


def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from session"""
    return request.session.get("user")


def require_auth(request: Request) -> dict:
    """Dependency to require authentication"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


def require_auth_redirect(request: Request) -> dict:
    """Dependency to require authentication with redirect"""
    user = get_current_user(request)
    if not user:
        # For HTML pages, redirect to login
        return RedirectResponse(url=f"/auth/login?next={request.url.path}", status_code=303)
    return user


def require_admin(request: Request) -> dict:
    """Dependency to require admin role"""
    user = require_auth(request)
    if user.get("role") != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


def is_authenticated(request: Request) -> bool:
    """Check if user is authenticated"""
    return get_current_user(request) is not None


def is_admin(request: Request) -> bool:
    """Check if user is admin"""
    user = get_current_user(request)
    return user is not None and user.get("role") == "Admin"