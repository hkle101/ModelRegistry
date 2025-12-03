from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
import logging

from backend.deps import storage_manager, verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


# ------------------------------
# Request Model
# ------------------------------
class ArtifactRegExRequest(BaseModel):
    regex: str


# ------------------------------
# Endpoint: /artifact/byRegEx
# ------------------------------
@router.post("/artifact/byRegEx")
def artifact_by_regex(
    regex_request: ArtifactRegExRequest = Body(...),
    _: bool = Depends(verify_token),
):
    """
    Search for artifacts by regex over names + README content.
    """
    pattern = regex_request.regex

    # Validate input
    if not pattern:
        raise HTTPException(status_code=400, detail="Missing or invalid regex field")

    logger.info(f"🔍 API regex search requested: pattern='{pattern}'")

    try:
        # Run regex search (this calls DynamoDB + README checks)
        matched_items = storage_manager.search_artifacts_by_regex(pattern)

        if not matched_items:
            logger.warning(f"⚠️ No artifacts found matching regex: {pattern}")
            raise HTTPException(status_code=404, detail="No artifact found under this regex")

        # Format response exactly matching ArtifactMetadata
        response = []
        for item in matched_items:
            response.append({
                "name": item.get("name"),
                "id": item.get("artifact_id"),
                "type": item.get("type") or item.get("artifact_type"),
            })

        logger.info(f"✅ Regex search matched {len(response)} artifacts")

        return response

    except ValueError as e:
        # Raised by storage_manager for invalid regex patterns
        logger.error(f"❌ Regex error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except HTTPException:
        # Let explicit HTTP errors pass through
        raise

    except Exception as e:
        logger.exception("❌ Unexpected error during regex search")
        raise HTTPException(status_code=500, detail=f"Error during regex search: {e}")