"""Health API router.

Provides a minimal liveness endpoint for the backend service.
"""

from fastapi import APIRouter, Response, status
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health_check():
    """Return HTTP 200 if the service is up."""
    logger.info("Health endpoint called")
    return Response(status_code=status.HTTP_200_OK)
