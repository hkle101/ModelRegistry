"""License check API router.

Validates an artifact exists and performs a lightweight reachability check
against a provided GitHub URL.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import requests
import logging
from backend.deps import storage_manager, verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


class SimpleLicenseCheckRequest(BaseModel):
    """Request payload containing a GitHub URL to check."""
    github_url: str


@router.post("/artifact/model/{id}/license-check")
def artifact_license_check(id: str, request: SimpleLicenseCheckRequest, _: bool = Depends(verify_token)):
    """Validate artifact existence and GitHub URL reachability."""
    try:
        artifact = storage_manager.get_artifact(id)
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")
        if not request.github_url or not isinstance(request.github_url, str):
            raise HTTPException(status_code=400, detail="Malformed request: github_url missing or invalid")
        try:
            response = requests.head(request.github_url, timeout=5)
            if response.status_code >= 400:
                raise HTTPException(status_code=502, detail="External license information could not be retrieved")
        except requests.RequestException:
            raise HTTPException(status_code=502, detail="External license information could not be retrieved")
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("License check failed")
        raise HTTPException(status_code=400, detail=str(e))