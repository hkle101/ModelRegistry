"""Authentication helpers (placeholder).

Provide functions for token validation and user extraction in requests.
"""

from typing import Dict, Any


def validate_token(token: str) -> Dict[str, Any]:
    """Validate a token string and return user info (placeholder)."""
    return {"sub": "anonymous"}
