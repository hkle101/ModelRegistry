from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
import re
import logging
from backend.deps import storage_manager, verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


class ArtifactRegExRequest(BaseModel):
    regex: str


@router.post("/artifact/byRegEx")
def artifact_by_regex(regex_request: ArtifactRegExRequest = Body(...), _: bool = Depends(verify_token)):
    try:
        pattern = regex_request.regex
        if not pattern:
            raise HTTPException(status_code=400, detail="Missing or invalid regex field")
        artifacts = storage_manager.list_artifacts()
        matched = []
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            raise HTTPException(status_code=400, detail=f"Invalid regex pattern: {e}")
        for artifact in artifacts:
            name = artifact.get("name", "")
            if compiled.search(name):
                matched.append({
                    "id": artifact.get("id") or artifact.get("artifact_id"),
                    "name": name,
                    "type": artifact.get("type") or artifact.get("artifact_type"),
                })
        if not matched:
            raise HTTPException(status_code=404, detail="No artifact found under this regex")
        return matched
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Regex search failed")
        raise HTTPException(status_code=500, detail=f"Error during regex search: {e}")