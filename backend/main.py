import os
import json
import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Header, Depends, status
from pydantic import BaseModel
from cli.utils.ArtifactManager import ArtifactManager
from backend.services.storage import StorageManager

# ------------------------
# Logging
# ------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ------------------------
# Configuration
# ------------------------
UPLOAD_TOKEN = os.getenv("UPLOAD_TOKEN", "my_secret_token")
app = FastAPI(title="ModelRegistry Backend")

# ------------------------
# Models
# ------------------------
class ArtifactUploadRequest(BaseModel):
    url: str
    filename: Optional[str] = None  # optional name for testing

class ArtifactQuery(BaseModel):
    name: str
    types: Optional[List[str]] = None

# ------------------------
# Managers
# ------------------------
artifact_manager = ArtifactManager()
storage_manager = StorageManager()

# ------------------------
# Dependencies
# ------------------------
def verify_token(x_authorization: str = Header(None, convert_underscores=False)):
    if x_authorization != UPLOAD_TOKEN:
        logger.warning("Unauthorized access attempt")
        raise HTTPException(status_code=403, detail="Authentication failed")
    return True

# ------------------------
# Endpoints
# ------------------------
@app.get(
    "/health",
    summary="Heartbeat check (BASELINE)",
    description="Lightweight liveness probe. Returns HTTP 200 when the registry API is reachable.",
    response_description="Service reachable."
)
def health_check():
    return {"status": "ok"}


@app.post("/artifact/{artifact_type}", status_code=status.HTTP_201_CREATED)
def artifact_create(
    artifact_type: str,
    request: ArtifactUploadRequest,
    _: bool = Depends(verify_token),
):
    try:
        # Extract metadata from URL
        artifact_data = artifact_manager.processUrl(request.url)
        artifact_data["artifact_type"] = artifact_type

        # Convert to JSON bytes for storage
        artifact_bytes = json.dumps(artifact_data, indent=2).encode("utf-8")

        # Store artifact
        success = storage_manager.store_artifact(artifact_data, artifact_bytes, request.filename)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to store artifact")

        logger.info(f"Stored artifact '{artifact_data.get('name')}' ({artifact_data.get('artifact_id')})")
        return {
            "metadata": {
                "name": artifact_data.get("name"),
                "id": artifact_data.get("artifact_id"),
                "type": artifact_type
            },
            "data": {
                "url": request.url
            }
        }

    except Exception as e:
        logger.exception("Artifact creation failed")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/artifacts")
def artifacts_list(
    queries: List[ArtifactQuery],
    offset: Optional[str] = None,
    _: bool = Depends(verify_token),
):
    try:
        items = storage_manager.list_artifacts(queries, offset)
        logger.info(f"Returned {len(items)} artifacts")
        return items
    except Exception as e:
        logger.exception("Failed to list artifacts")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/artifacts/{artifact_id}")
def artifact_retrieve(
    artifact_id: str,
    _: bool = Depends(verify_token),
):
    try:
        artifact = storage_manager.get_artifact(artifact_id)
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")
        return artifact
    except Exception as e:
        logger.exception(f"Failed to retrieve artifact '{artifact_id}'")
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/artifacts/{artifact_id}")
def artifact_update(
    artifact_id: str,
    request: ArtifactUploadRequest,
    _: bool = Depends(verify_token),
):
    try:
        artifact_data = artifact_manager.processUrl(request.url)
        artifact_data["artifact_id"] = artifact_id
        artifact_data["artifact_type"] = artifact_data.get("artifact_type")  # preserve type

        artifact_bytes = json.dumps(artifact_data, indent=2).encode("utf-8")
        success = storage_manager.update_artifact(artifact_data, artifact_bytes, request.filename)
        if not success:
            raise HTTPException(status_code=404, detail="Artifact not found or update failed")
        return {"status": "updated", "artifact_id": artifact_id}

    except Exception as e:
        logger.exception(f"Artifact update failed for '{artifact_id}'")
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/artifacts/{artifact_id}")
def artifact_delete(
    artifact_id: str,
    _: bool = Depends(verify_token),
):
    try:
        success = storage_manager.delete_artifact(artifact_id)
        if not success:
            raise HTTPException(status_code=404, detail="Artifact not found or delete failed")
        return {"status": "deleted", "artifact_id": artifact_id}
    except Exception as e:
        logger.exception(f"Artifact deletion failed for '{artifact_id}'")
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/reset")
def reset_registry(_: bool = Depends(verify_token)):
    """
    Reset the registry to a system default state.
    Used for testing/autograder.
    """
    try:
        success = storage_manager.reset()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to reset registry")
        return {"status": "reset"}
    except Exception as e:
        logger.exception("Registry reset failed")
        raise HTTPException(status_code=400, detail=str(e))

