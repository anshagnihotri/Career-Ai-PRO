"""
modules/auth.py — Authentication system for CareerAI Pro.
Handles user signup, login, and input validation.
"""

import logging
import re
from typing import Optional

import bcrypt

from utils import db

logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def _check_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def _validate_email(email: str) -> bool:
    return bool(re.match(r"^[\w.+\-]+@[\w\-]+\.[a-zA-Z]{2,}$", email))


def signup_user(name: str, email: str, password: str) -> tuple[bool, list[str]]:
    """
    Register a new user.
    Returns (success, list_of_messages).
    """
    errors = []
    name = name.strip()
    email = email.strip().lower()
    password = password.strip()

    if not name or len(name) < 2:
        errors.append("Name must be at least 2 characters.")
    if not _validate_email(email):
        errors.append("Please enter a valid email address.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if errors:
        return False, errors

    if db.get_user_by_email(email):
        return False, ["An account with this email already exists."]

    try:
        password_hash = _hash_password(password)
        db.create_user(name, email, password_hash)
        return True, ["Account created! Please log in."]
    except Exception as exc:
        logger.exception("Signup error")
        return False, [f"Signup failed: {exc}"]


def login_user(email: str, password: str) -> tuple[bool, list[str], Optional[dict]]:
    """
    Authenticate a user.
    Returns (success, list_of_messages, user_dict_or_None).
    """
    email = email.strip().lower()
    password = password.strip()

    if not email or not password:
        return False, ["Please fill in all fields."], None

    user = db.get_user_by_email(email)
    if not user:
        return False, ["No account found with that email."], None

    if not _check_password(password, user["password_hash"]):
        return False, ["Incorrect password. Please try again."], None

    return True, [f"Welcome back, {user['name']}! 👋"], user
