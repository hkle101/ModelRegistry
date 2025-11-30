from fastapi import APIRouter, Depends, HTTPException
import logging
from backend.deps import storage_manager, verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/artifacts/{artifact_type}/{id}")
def artifact_retrieve(artifact_type: str, id: str, _: bool = Depends(verify_token)):
    """Retrieve a single artifact by type and ID."""
    try:
        artifact = storage_manager.get_artifact(id)
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")
        if artifact.get("type") != artifact_type:
            raise HTTPException(status_code=400, detail="Artifact type mismatch")
        return {
            "metadata": {
                "name": artifact.get("name"),
                "id": artifact.get("artifact_id"),
                "type": artifact.get("type"),
            },
            "data": {"url": artifact.get("processed_url")},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Artifact retrieve failed")
        raise HTTPException(status_code=400, detail=f"Failed to retrieve artifact {e}")