"""Delete API router.

Deletes an artifact (metadata + stored bytes) from the registry.
"""

from fastapi import APIRouter, Depends, HTTPException, Path
from backend.deps import storage_manager, verify_token

router = APIRouter()


@router.delete("/artifacts/{artifact_type}/{id}")
def delete_artifact(
    artifact_type: str = Path(..., description="Type of artifact to delete"),
    id: str = Path(..., description="Artifact ID"),
    _: bool = Depends(verify_token)
):
    """Delete an artifact by type + id."""
    # Validate artifact_type
    if artifact_type not in ["model", "dataset", "code"]:
        raise HTTPException(status_code=400, detail="Invalid artifact_type")

    if not id:
        raise HTTPException(status_code=400, detail="Missing artifact_id")

    # Attempt deletion
    success = storage_manager.delete_artifact(id)
    if not success:
        raise HTTPException(status_code=404, detail="Artifact does not exist")

    # Success: return 200 with empty body (as per spec)
    return {}
