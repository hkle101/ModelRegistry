"""Pydantic models used by backend API endpoints."""

from pydantic import BaseModel
from typing import Dict, Any


class MetricResult(BaseModel):
    name: str
    category: str
    net_score: float
    details: Dict[str, Any] = {}
