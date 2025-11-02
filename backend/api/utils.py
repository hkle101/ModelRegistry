"""Small utilities used by API endpoints (serializers, helpers)."""

from typing import Dict, Any


def normalize_result(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw metric dict into API-friendly shape."""
    return {
        "name": raw.get("name", ""),
        "category": raw.get("category", "UNKNOWN"),
        "net_score": raw.get("net_score", 0.0),
        "details": {k: v for k, v in raw.items() if k not in ["name", "category", "net_score"]},
    }
