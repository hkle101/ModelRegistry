# backend/app/auth.py
import secrets
from datetime import datetime, timedelta
from typing import Dict

# Simple in-memory token store
TOKENS: Dict[str, Dict] = {}

def generate_token(user_id: str = "anonymous", expires_minutes: int = 60) -> str:
    """
    Generates a secure token for a user that expires in `expires_minutes`.
    """
    token = secrets.token_urlsafe(32)
    TOKENS[token] = {
        "user_id": user_id,
        "expires_at": datetime.utcnow() + timedelta(minutes=expires_minutes)
    }
    return token

def validate_token(token: str) -> bool:
    """
    Checks if a token exists and is not expired.
    """
    info = TOKENS.get(token)
    if not info:
        return False
    if info["expires_at"] < datetime.utcnow():
        del TOKENS[token]
        return False
    return True
