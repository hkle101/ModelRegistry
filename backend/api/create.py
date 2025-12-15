"""Create API router.

Provides artifact registration via URL ingestion and persists metadata/content
through the shared storage layer.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel
import requests
import logging
from backend.deps import artifact_manager, storage_manager, verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


class ArtifactUploadRequest(BaseModel):
    """
    Request schema for uploading an artifact.

    Attributes:
        name (str, optional): Optional human-readable name for the artifact.
        url (str): The URL of the artifact to fetch metadata and download.
    """
    name: str | None = None
    url: str


@router.post("/artifact/{artifact_type}", status_code=status.HTTP_201_CREATED)
def artifact_create(
    artifact_type: str,
    request: ArtifactUploadRequest,
    http_request: Request,
    _: bool = Depends(verify_token),
):
    """
    Register a new artifact and store both its metadata and actual content.

    Steps:
    1. Use the artifact URL to fetch metadata via `artifact_manager`.
    2. Extract `download_url` from metadata.
    3. Fetch the actual artifact bytes from `download_url`.
    4. Store artifact data and bytes in storage (S3 + DynamoDB).
    5. Return stored metadata and download information.

    Args:
        artifact_type (str): Type/category of the artifact (e.g., 'model', 'dataset', 'code').
        request (ArtifactUploadRequest): Pydantic model containing artifact URL and optional name.
        http_request (Request): FastAPI request object (can be used for logging or context).
        _ (bool): Dependency that verifies the request token (via `verify_token`).

    Returns:
        dict: Contains metadata of the stored artifact and URLs.

    Raises:
        HTTPException: If fetching metadata, downloading artifact, or storing fails.
    """
    try:
        # Step 1: Process the artifact URL to get metadata
        artifact_data = artifact_manager.processUrl(request.url)
        artifact_id = artifact_data.get("artifact_id")
        download_url = artifact_data.get("download_url")
        artifact_data["artifact_type"] = artifact_type
        artifact_data["processed_url"] = request.url
        if request.name:
            artifact_data["name"] = request.name

        # Step 2: Fetch artifact bytes from download_url
        if not download_url:
            raise HTTPException(
                status_code=400,
                detail="No download URL found for the artifact"
            )

        response = requests.get(download_url, stream=True)
        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch artifact bytes from {download_url}"
            )

        # Step 3: Convert artifact content to bytes
        artifact_bytes = response.content

        # Step 4: Store artifact in S3 + DynamoDB
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

        # Step 5: Fetch stored metadata
        stored_metadata = storage_manager.get_artifact(artifact_data.get("artifact_id"))
        if not stored_metadata:
            raise HTTPException(
                status_code=500, detail="Artifact stored but metadata missing"
            )

        # Return metadata and download information
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
