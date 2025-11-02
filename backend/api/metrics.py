"""API router exposing metric scoring endpoints."""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()


@router.get("/score")
def score_url(url: str) -> Dict[str, Any]:
    """Score a single URL and return a dict with scores and metadata.

    Placeholder implementation that should call MetricScorer/MetricDataFetcher.
    """
    # TODO: wire MetricScorer here
    return {"name": url, "net_score": 0.0, "category": "UNKNOWN"}
