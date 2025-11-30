from fastapi import APIRouter, Response, status
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health_check():
    logger.info("Health endpoint called")
    return Response(status_code=status.HTTP_200_OK)
