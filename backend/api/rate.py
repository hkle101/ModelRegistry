from fastapi import APIRouter, Depends, HTTPException
import logging
import json
from backend.deps import storage_manager, verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/artifact/model/{id}/rate")
def artifact_model_rate(id: str, _: bool = Depends(verify_token)):
    try:
        if not id:
            raise HTTPException(status_code=400, detail="Missing artifact_id")

        artifact = storage_manager.get_artifact(id)
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact does not exist")

        name = artifact.get("name", "unknown")
        category = artifact.get("artifact_type") or artifact.get("type") or "model"

        # If scores were stored with the artifact, return them (prefer stored)
        scores = artifact.get("scores")
        if scores:
            # stored scores may be JSON string or dict
            if isinstance(scores, str):
                try:
                    scores = json.loads(scores)
                except Exception:
                    # leave as string if parsing fails
                    pass

            if isinstance(scores, dict):
                scores.setdefault("name", name)
                scores.setdefault("category", category)
                return scores

        # Otherwise, attempt to recompute scores using the ArtifactManager
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
            # Fetch artifact data and compute scores using existing scorer
            artifact_data = storage_manager.artifact_manager.getArtifactData(
                processed_url
            )
            computed = storage_manager.artifact_manager.scoreArtifact(artifact_data)

            # MetricScorer returns a JSON string by default
            if isinstance(computed, str):
                try:
                    computed = json.loads(computed)
                except Exception:
                    # fallback to an error
                    logger.exception("Failed to parse computed scores JSON")
                    raise HTTPException(
                        status_code=500, detail="Failed to compute ratings"
                    )

            if isinstance(computed, dict):
                computed.setdefault("name", name)
                computed.setdefault("category", category)
                return computed
            else:
                raise HTTPException(status_code=500, detail="Unexpected score format")

        except HTTPException:
            raise
        except Exception:
            logger.exception("Rating computation failed")
            raise HTTPException(status_code=500, detail="Internal rating error")

    except HTTPException:
        # propagate expected HTTP errors
        raise
    except Exception:
        logger.exception("Unhandled error in artifact_model_rate")
        raise HTTPException(status_code=500, detail="Internal server error")
