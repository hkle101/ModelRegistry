# backend/main.py
import os
import logging
from fastapi import FastAPI, HTTPException, Header, Query, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from backend.app.models import ArtifactData, ArtifactRegEx, Artifact
from backend.app.crud import (
    create_artifact,
    read_artifact,
    update_artifact_metadata,
    delete_artifact_by_id,
    list_all_artifacts,
    search_artifacts_by_query,
)
from cli.utils.ArtifactManager import ArtifactManager

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ------------------------
# Configuration
# ------------------------
UPLOAD_TOKEN = os.getenv("UPLOAD_TOKEN", "my_secret_token")  # default for dev

app = FastAPI(title="ModelRegistry Backend")


# ------------------------
# Models
# ------------------------
class ArtifactUploadRequest(BaseModel):
    url: str  # URL of HuggingFace model, dataset, or GitHub repo


# ------------------------
# Artifact CRUD Endpoints (6 supported)
# ------------------------


artifact_manager = ArtifactManager()

@app.post("/artifact/{artifact_type}")
def artifact_create(
    artifact_type: str,
    request: ArtifactData,
    x_authorization: str = Header(None, convert_underscores=False),
):
    if x_authorization != UPLOAD_TOKEN:
        raise HTTPException(status_code=403, detail="Authentication failed")
    
    try:
        # Process the URL to extract metadata
        processed = artifact_manager.process_url(request.url)
        # Add artifact_type to the processed data
        processed["type"] = artifact_type
        
        # Now create artifact with fully processed data
        created = create_artifact(processed)
        return created
    except Exception as e:
        logger.exception("Artifact create failed")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/artifacts/{artifact_type}/{artifact_id}")
def artifact_retrieve(
    artifact_type: str,
    artifact_id: str,
    x_authorization: str = Header(None, convert_underscores=False),
):
    """Retrieve a specific artifact by ID"""
    if x_authorization != UPLOAD_TOKEN:
        raise HTTPException(status_code=403, detail="Authentication failed")
    artifact = read_artifact(artifact_type, artifact_id)
    if not artifact:
        logger.warning(f"Artifact not found: {artifact_id} (type={artifact_type})")
        raise HTTPException(status_code=404, detail="Artifact not found")
    logger.info(f"Artifact retrieved: {artifact_id} (type={artifact_type})")
    return artifact


@app.put("/artifacts/{artifact_type}/{artifact_id}")
def artifact_update(
    artifact_type: str,
    artifact_id: str,
    payload: Artifact,
    x_authorization: str = Header(None, convert_underscores=False),
):
    """Update artifact metadata"""
    if x_authorization != UPLOAD_TOKEN:
        raise HTTPException(status_code=403, detail="Authentication failed")
    try:
        success = update_artifact_metadata(artifact_type, artifact_id, payload.dict())
        if not success:
            logger.warning(f"Artifact not found for update: {artifact_id} (type={artifact_type})")
            raise HTTPException(status_code=404, detail="Artifact not found")
        logger.info(f"Artifact updated: {artifact_id} (type={artifact_type})")
        return {"status": "updated"}
    except Exception as e:
        logger.exception("Artifact update failed")
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/artifact/{artifact_type}/{artifact_id}")
def artifact_delete(
    artifact_type: str,
    artifact_id: str,
    x_authorization: str = Header(None, convert_underscores=False),
):
    """Delete an artifact by ID"""
    if x_authorization != UPLOAD_TOKEN:
        raise HTTPException(status_code=403, detail="Authentication failed")
    success = delete_artifact_by_id(artifact_type, artifact_id)
    if not success:
        logger.warning(f"Artifact not found for deletion: {artifact_id} (type={artifact_type})")
        raise HTTPException(status_code=404, detail="Artifact not found")
    logger.info(f"Artifact deleted: {artifact_id} (type={artifact_type})")
    return {"status": "deleted"}


@app.post("/artifacts")
def artifacts_list(
    x_authorization: str = Header(None, convert_underscores=False),
    offset: str | None = Query(None),
):
    """List artifacts with pagination (offset/limit)"""
    if x_authorization != UPLOAD_TOKEN:
        raise HTTPException(status_code=403, detail="Authentication failed")
    off = int(offset) if offset else 0
    try:
        items = list_all_artifacts(limit=10, offset=off)
        logger.info(f"Artifacts listed: {len(items)} items (offset={off})")
        resp: Response = JSONResponse(content=items)
        resp.headers["offset"] = str(off + len(items))
        return resp
    except Exception as e:
        logger.exception("Artifacts list failed")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/artifact/byRegEx")
def artifact_by_regex(
    request: ArtifactRegEx,
    x_authorization: str = Header(None, convert_underscores=False),
):
    """Search artifacts by regex"""
    if x_authorization != UPLOAD_TOKEN:
        raise HTTPException(status_code=403, detail="Authentication failed")
    try:
        results = search_artifacts_by_query(request.regex)
        logger.info(f"Artifact regex search: {len(results)} results for regex={request.regex}")
        return results
    except Exception as e:
        logger.exception("Artifact regex search failed")
        raise HTTPException(status_code=400, detail=str(e))
