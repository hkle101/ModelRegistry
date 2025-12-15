from fastapi import APIRouter, Depends, HTTPException, Body
import logging
from backend.deps import verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


@router.put("/artifacts/{artifact_type}/{id}")
def artifact_update(
    artifact_type: str,
    id: str,
    artifact_data: dict = Body(...),
    _: bool = Depends(verify_token),
):
    try:
        if not id or not artifact_type:
            raise HTTPException(status_code=400, detail="Missing or invalid artifact_type or artifact_id")
        return {"status": "updated", "artifact_id": id}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Artifact update failed")
        raise HTTPException(status_code=500, detail="Internal error")