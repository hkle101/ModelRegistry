import os
import json
import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Header, Depends, status, Response, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from cli.utils.ArtifactManager import ArtifactManager
from backend.services.storage import StorageManager

# ============================================================
# Logging
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")

# ============================================================
# Configuration
# ============================================================
UPLOAD_TOKEN = os.getenv("UPLOAD_TOKEN")  # token optional for baseline
app = FastAPI(title="Model Registry Backend")

# ============================================================
# CORS
# ============================================================
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Pydantic Models
# ============================================================
class ArtifactUploadRequest(BaseModel):
    url: str

class ArtifactQuery(BaseModel):
    name: Optional[str] = None
    types: Optional[List[str]] = None

# ============================================================
# Managers
# ============================================================
artifact_manager = ArtifactManager()
storage_manager = StorageManager()

# ============================================================
# Token Dependency (optional)
# ============================================================
def verify_token(x_authorization: str = Header(None, convert_underscores=False)):
    """
    baseline requires no token, so always return True
    """
    return True

# ============================================================
# Endpoints
# ============================================================

@app.get("/health")
def health_check():
    return Response(status_code=status.HTTP_200_OK)


# --------------------------- CREATE ---------------------------
@app.post("/artifact/{artifact_type}", status_code=status.HTTP_201_CREATED)
def artifact_create(
    artifact_type: str,
    request: ArtifactUploadRequest,
    _: bool = Depends(verify_token),
):
    """
    Register a new artifact by providing a downloadable source URL.
    Returns 201 if processed immediately, 202 if rating is deferred.
    """
    try:
        # Process artifact: fetch metadata and compute scores
        artifact_data = artifact_manager.processUrl(request.url)
        artifact_data["artifact_type"] = artifact_type
        artifact_data["processed_url"] = request.url
        # Convert artifact data to bytes
        artifact_bytes = json.dumps(artifact_data, indent=2).encode("utf-8")
        # Store artifact (metadata + bytes)
        storage_success = storage_manager.store_artifact(
            artifact_data, artifact_bytes, artifact_data.get("name")
        )
        if not storage_success:
            raise HTTPException(status_code=500, detail="Failed to store artifact")

        # Log stored artifact
        logger.info(
            f"Stored artifact {artifact_data.get('artifact_id')} of type {artifact_type}"
        )
        download_url = storage_manager.generate_download_url(
            artifact_data.get("artifact_id"), artifact_data.get("name")
        )
        # Immediate processing: 201 Created
        return {
            "metadata": {
                "name": artifact_data.get("name"),
                "id": artifact_data.get("artifact_id"),
                "type": artifact_type,
            },
            "data": {
                "url": request.url,
                "download_url": download_url,
            },
        }
    except HTTPException as he:
        # Re-raise known HTTP exceptions
        raise he
    except Exception as e:
        logger.exception("Artifact creation failed")
        raise HTTPException(status_code=400, detail=str(e))

# --------------------------- LIST ---------------------------
@app.post("/artifacts")
def artifacts_list(
    response: Response,
    queries: Optional[List[ArtifactQuery]] = Body(default=None),
    offset: Optional[str] = Query(None),
    _: bool = Depends(verify_token),
):
    try:
        items = storage_manager.list_artifacts(queries)

        # Set next offset in header (stub)
        next_offset = str(len(items)) if items else "0"
        response.headers["offset"] = next_offset

        logger.info(f"Returned {len(items)} artifacts")
        return items

    except Exception as e:
        logger.exception("Failed to list artifacts")
        raise HTTPException(status_code=400, detail=str(e))

# --------------------------- RETRIEVE ---------------------------
@app.get("/artifacts/{artifact_type}/{id}")
def artifact_retrieve(
    artifact_type: str,
    id: str,
    _: bool = Depends(verify_token),
):
    """
    Retrieve a single artifact by type and ID.
    """
    try:
        artifact = storage_manager.get_artifact(id)
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")

        # Check artifact type matches
        if artifact.get("type") != artifact_type:
            raise HTTPException(status_code=400, detail="Artifact type mismatch")

        # Return in expected format
        return {
            "metadata": {
                "name": artifact.get("name"),
                "id": artifact.get("artifact_id"),
                "type": artifact.get("type"),
            },
            "data": {
                "url": artifact.get("processed_url"),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Artifact retrieve failed")
        raise HTTPException(status_code=400, detail=f"Failed to retrieve artifact {e}")

# --------------------------- DELETE ---------------------------
@app.delete("/artifacts/{artifact_id}")
def artifact_delete(
    artifact_id: str,
    _: bool = Depends(verify_token)
):
    try:
        success = storage_manager.delete_artifact(artifact_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Artifact not found or delete failed"
            )

        return {"status": "deleted", "artifact_id": artifact_id}

    except Exception as e:
        logger.exception("Artifact deletion failed")
        raise HTTPException(status_code=400, detail=str(e))


# --------------------------- RESET ---------------------------
@app.delete("/reset", status_code=200)
def reset_registry(
    user_has_permission: bool = Depends(verify_token),
):
    logger.info("🔄 Reset request received")
    # --- If token is valid but user lacks permission (401) ---
    if not user_has_permission:
        logger.warning("⛔ Reset denied: user lacks reset permission (401)")
        raise HTTPException(status_code=401, detail="Not authorized to reset")
    # --- Perform reset ---
    try:
        success = storage_manager.reset()
        if not success:
            logger.error("❌ Reset failed: storage_manager returned False")
            raise HTTPException(status_code=500, detail=" Reset failed")

        logger.info("✅ Registry successfully reset")
        return {"message": "Registry reset"}

    except Exception as e:
        logger.exception(f"🔥 Exception during reset: {e}")
        raise HTTPException(status_code=500, detail="Internal error")