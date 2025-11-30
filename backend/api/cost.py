from fastapi import APIRouter, Depends, HTTPException
import random
import logging
from backend.deps import storage_manager, verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/artifact/{artifact_type}/{id}/cost")
def artifact_cost(artifact_type: str, id: str, _: bool = Depends(verify_token)):
    try:
        if not id or not artifact_type:
            raise HTTPException(status_code=400, detail="Missing or invalid artifact_type or artifact_id")
        artifact = storage_manager.get_artifact(id)
        if not artifact:
            raise HTTPException(status_code=404, detail=f"Artifact {id} of type {artifact_type} does not exist")
        total_cost = round(random.uniform(400, 900), 1)
        return {"artifact_id": id, "type": artifact_type, "total_cost": total_cost}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to compute cost")
        raise HTTPException(status_code=500, detail="Internal error")