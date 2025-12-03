"""
User service - User management business logic
"""
from typing import Optional, Dict, Any
import bcrypt

from db import fetch_one, fetch_all, execute, transaction


def get_user_by_id(db, user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    return fetch_one(
        db,
        "SELECT user_id, username, email, full_name, role, registration_date FROM user WHERE user_id = %s",
        (user_id,)
    )


def get_user_by_email(db, email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    return fetch_one(
        db,
        "SELECT user_id, username, email, password_hash, full_name, role FROM user WHERE email = %s",
        (email,)
    )


def create_user(db, username: str, email: str, password: str, full_name: str, role: str = "Customer") -> int:
    """
    Create a new user with hashed password.

    Returns:
        user_id of the newly created user
    """
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    with transaction(db):
        user_id = execute(
            db,
            """
            INSERT INTO user (username, email, password_hash, full_name, role)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (username, email, password_hash, full_name, role)
        )

    return user_id


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def authenticate_user(db, email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user with email and password.

    Returns:
        User dict if authentication successful, None otherwise
    """
    user = get_user_by_email(db, email)

    if not user:
        return None

    if not verify_password(password, user['password_hash']):
        return None

    # Remove password_hash from returned user dict
    user.pop('password_hash', None)

    return user