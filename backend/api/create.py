from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
import json
import logging
from backend.deps import artifact_manager, storage_manager, verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


class ArtifactUploadRequest(BaseModel):
    url: str


@router.post("/artifact/{artifact_type}", status_code=status.HTTP_201_CREATED)
def artifact_create(
    artifact_type: str,
    request: ArtifactUploadRequest,
    _: bool = Depends(verify_token),
):
    """Register a new artifact and store metadata + bytes."""
    try:
        # Process the artifact URL to get metadata
        artifact_data = artifact_manager.processUrl(request.url)
        artifact_data["artifact_type"] = artifact_type
        artifact_data["processed_url"] = request.url

        # Convert artifact data to bytes for storage
        artifact_bytes = json.dumps(artifact_data, indent=2).encode("utf-8")

        # Store artifact in S3 + DynamoDB (includes download_url in metadata)
        ok = storage_manager.store_artifact(
            artifact_data, artifact_bytes, artifact_data.get("name")
        )
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to store artifact")

        logger.info(
            "Stored artifact %s of type %s",
            artifact_data.get("artifact_id"),
            artifact_type,
        )

        # Fetch stored metadata to return to the user
        stored_metadata = storage_manager.get_artifact(artifact_data.get("artifact_id"))
        if not stored_metadata:
            raise HTTPException(status_code=500, detail="Artifact stored but metadata missing")

        return {
            "metadata": {
                "name": stored_metadata.get("name"),
                "id": stored_metadata.get("artifact_id"),
                "type": stored_metadata.get("type"),
            },
            "data": {
                "url": request.url,
                "download_url": stored_metadata.get("download_url"),
            },
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Artifact creation failed")
        raise HTTPException(status_code=400, detail=str(e))
