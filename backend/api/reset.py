"""Reset API router.

Provides an administrative endpoint to clear registry storage.
"""

from fastapi import APIRouter, Depends, HTTPException
import logging
from backend.deps import storage_manager, verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


@router.delete("/reset", status_code=200)
def reset_registry(user_has_permission: bool = Depends(verify_token)):
    """Reset (clear) storage for the registry."""
    logger.info("Reset request received")
    if not user_has_permission:
        logger.warning("Reset denied: user lacks permission")
        raise HTTPException(status_code=401, detail="Not authorized to reset")
    try:
        success = storage_manager.reset()
        if not success:
            logger.error("Reset failed: storage_manager returned False")
            raise HTTPException(status_code=500, detail="Reset failed")
        logger.info("Registry successfully reset")
        return {"message": "Registry reset"}
    except Exception as e:
        logger.exception("Exception during reset")
        raise HTTPException(status_code=500, detail="Internal error")