from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel
import json
import logging
from backend.deps import artifact_manager, storage_manager, verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


class ArtifactUploadRequest(BaseModel):
    name: str | None = None
    url: str


@router.post("/artifact/{artifact_type}", status_code=status.HTTP_201_CREATED)
def artifact_create(
    artifact_type: str,
    request: ArtifactUploadRequest,
    http_request: Request,
    _: bool = Depends(verify_token),
):
    """Register a new artifact and store metadata + bytes."""
    try:
        # Process the artifact URL to get metadata
        artifact_data = artifact_manager.processUrl(request.url)
        artifact_id_val = artifact_data.get("artifact_id")
        if not isinstance(artifact_id_val, str):
            raise HTTPException(status_code=500, detail="Invalid artifact_id returned from artifact manager")
        artifact_id = artifact_id_val
        # ✅ CLEAN DOWNLOAD URL (new format)
        base_url = str(http_request.base_url).rstrip("/")
        download_url = f"{base_url}/artifact/{artifact_id}/download"
        artifact_data["artifact_type"] = artifact_type
        artifact_data["processed_url"] = request.url
        artifact_data["download_url"] = download_url
        if request.name:
            artifact_data["name"] = request.name

        # Convert artifact data to bytes for storage
        artifact_bytes = json.dumps(artifact_data, indent=2).encode("utf-8")

        # Store artifact in S3 + DynamoDB
        ok = storage_manager.store_artifact(
            artifact_data,
            artifact_bytes,
            artifact_data.get("name"),
        )
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to store artifact")

        logger.info(
            "Stored artifact %s of type %s",
            artifact_data.get("artifact_id"),
            artifact_type,
        )

        # Fetch stored metadata
        stored_metadata = storage_manager.get_artifact(artifact_id)
        if not stored_metadata:
            raise HTTPException(
                status_code=500, detail="Artifact stored but metadata missing"
            )

        return {
            "metadata": {
                "name": stored_metadata.get("name"),
                "id": artifact_id,
                "type": stored_metadata.get("type"),
            },
            "data": {
                "url": request.url,
                "download_url": download_url,
            },
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Artifact creation failed")
        raise HTTPException(status_code=400, detail=str(e))
