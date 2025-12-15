"""Download API router.

Exposes a stable endpoint that redirects to a short-lived presigned S3 URL.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
import logging
from backend.deps import storage_manager, verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/artifact/{artifact_id}/download")
def download_artifact(
    artifact_id: str,
    _: bool = Depends(verify_token),
):
    """
    Returns a stable download endpoint for an artifact.
    Internally generates a short-lived presigned S3 URL and redirects to it.
    """
    try:
        artifact = storage_manager.get_artifact(artifact_id)
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact does not exist")

        filename = artifact.get("name")
        if not filename:
            raise HTTPException(status_code=500, detail="Artifact filename missing")

        presigned_url = storage_manager.generate_download_url(
            artifact_id=artifact_id,
            filename=filename,
        )

        return RedirectResponse(
            url=presigned_url,
            status_code=302
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to download artifact")
        raise HTTPException(
            status_code=500,
            detail="Failed to download artifact"
        )