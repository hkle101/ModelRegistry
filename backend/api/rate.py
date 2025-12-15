"""Rating API router.

Exposes scoring/ratings retrieval for a model artifact.
"""

from fastapi import APIRouter, Depends, HTTPException
import logging
import json
from backend.deps import storage_manager, verify_token

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/artifact/model/{id}/rate")
def artifact_model_rate(id: str, _: bool = Depends(verify_token)):
    """
    Retrieve the ratings/scores for a model artifact.
    Tries to use stored scores from DynamoDB if available, else recomputes.
    Ensures 'name' and 'category' are always populated.
    """
    try:
        logger.info(f"[RATE] Requested rating for artifact_id={id}")

        if not id:
            raise HTTPException(status_code=400, detail="Missing artifact_id")

        # Fetch artifact metadata from DynamoDB
        artifact = storage_manager.get_artifact(id)
        if not artifact:
            logger.warning(f"[RATE] Artifact {id} not found in storage")
            raise HTTPException(status_code=404, detail="Artifact does not exist")

        logger.info(f"[RATE] Retrieved metadata for {id}: {artifact}")

        # Determine fallback name and category
        fallback_name = artifact.get("name") or "unknown"
        fallback_category = artifact.get("artifact_type") or artifact.get("type") or "model"

        scores = artifact.get("scores")
        if scores:
            logger.info(f"[RATE] Found stored scores for {id}")

            # If stored as JSON string, parse it
            if isinstance(scores, str):
                logger.info(f"[RATE] Stored scores are JSON string — attempting parse")
                try:
                    scores = json.loads(scores)
                except Exception:
                    logger.exception(f"[RATE] Failed to parse stored scores for {id}")
                    scores = {}

            # Ensure name and category are populated
            if isinstance(scores, dict):
                if not scores.get("name") or scores.get("name") == "":
                    scores["name"] = fallback_name
                    logger.info(f"[RATE] Injected fallback name into scores: {fallback_name}")
                if not scores.get("category") or scores.get("category") == "":
                    scores["category"] = fallback_category
                    logger.info(f"[RATE] Injected fallback category into scores: {fallback_category}")

                logger.info(f"[RATE] Returning stored score response for {id}")
                return scores

        # If no scores stored, recompute using ArtifactManager
        logger.info(f"[RATE] No valid stored scores found — recomputing for {id}")

        processed_url = (
            artifact.get("processed_url")
            or artifact.get("download_url")
            or artifact.get("url")
        )
        if not processed_url:
            raise HTTPException(
                status_code=400,
                detail="No source URL available to compute ratings",
            )

        try:
            artifact_data = storage_manager.artifact_manager.getArtifactData(processed_url)
            computed = storage_manager.artifact_manager.scoreArtifact(artifact_data)

            # Parse if returned as JSON string
            if isinstance(computed, str):
                try:
                    computed = json.loads(computed)
                except Exception:
                    logger.exception(f"[RATE] Failed to parse computed scores JSON for {id}")
                    raise HTTPException(status_code=500, detail="Failed to compute ratings")

            if isinstance(computed, dict):
                computed["name"] = fallback_name
                computed["category"] = fallback_category
                logger.info(f"[RATE] Returning newly computed scores for {id}")
                return computed
            else:
                raise HTTPException(status_code=500, detail="Unexpected score format")

        except HTTPException:
            raise
        except Exception:
            logger.exception(f"[RATE] Rating computation failed for {id}")
            raise HTTPException(status_code=500, detail="Internal rating error")

    except HTTPException:
        raise
    except Exception:
        logger.exception(f"[RATE] Unhandled error in artifact_model_rate for {id}")
        raise HTTPException(status_code=500, detail="Internal server error")
