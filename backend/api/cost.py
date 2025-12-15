"""Cost API router.

Exposes an endpoint for estimating (or returning) an artifact cost payload.
Implementation details are owned by this project and may be placeholder.
"""

from fastapi import APIRouter, Depends, HTTPException
import logging
from backend.deps import storage_manager, verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/artifact/{artifact_type}/{id}/cost")
def artifact_cost(artifact_type: str, id: str, _: bool = Depends(verify_token)):
    """
    Compute the storage cost of an artifact based on its size in GB.

    Ensures that 'size_in_gb' is treated as a numeric value (float) even if stored as a string.
    Returns the total cost based on a fixed cost per GB.
    """
    try:
        if not id or not artifact_type:
            raise HTTPException(
                status_code=400,
                detail="Missing or invalid artifact_type or artifact_id"
            )

        artifact = storage_manager.get_artifact(id)
        if not artifact:
            raise HTTPException(
                status_code=404,
                detail=f"Artifact {id} of type {artifact_type} does not exist"
            )

        # Ensure size_in_gb is a number
        try:
            size_in_gb = float(artifact.get("size_in_gb", 0))
        except (ValueError, TypeError):
            logger.warning("Invalid size_in_gb for artifact %s: %s", id, artifact.get("size_in_gb"))
            size_in_gb = 0.0

        total_cost = size_in_gb

        return {
            id: {
                "size_in_gb": size_in_gb,
                "total_cost": total_cost
            }
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to compute cost")
        raise HTTPException(
            status_code=500,
            detail="The artifact cost calculator encountered an error"
        )