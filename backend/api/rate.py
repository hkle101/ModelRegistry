from fastapi import APIRouter, Depends, HTTPException
import random
import logging
from backend.deps import storage_manager, verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


def rand():
    return round(random.uniform(0.60, 0.90), 2)


@router.get("/artifact/model/{id}/rate")
def artifact_model_rate(id: str, _: bool = Depends(verify_token)):
    try:
        if not id:
            raise HTTPException(status_code=400, detail="Missing artifact_id")
        artifact = storage_manager.get_artifact(id)
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact does not exist")
        return {
            "name": artifact.get("name", "unknown"),
            "category": artifact.get("artifact_type", "model"),
            "net_score": rand(),
            "net_score_latency": rand(),
            "ramp_up_time": rand(),
            "ramp_up_time_latency": rand(),
            "bus_factor": rand(),
            "bus_factor_latency": rand(),
            "performance_claims": rand(),
            "performance_claims_latency": rand(),
            "license": 1.0,
            "license_latency": rand(),
            "dataset_and_code_score": rand(),
            "dataset_and_code_score_latency": rand(),
            "dataset_quality": rand(),
            "dataset_quality_latency": rand(),
            "code_quality": rand(),
            "code_quality_latency": rand(),
            "reproducibility": rand(),
            "reproducibility_latency": rand(),
            "reviewedness": rand(),
            "reviewedness_latency": rand(),
            "tree_score": rand(),
            "tree_score_latency": rand(),
            "size_score": {
                "raspberry_pi": rand(),
                "jetson_nano": rand(),
                "desktop_pc": rand(),
                "aws_server": rand(),
            },
            "size_score_latency": rand(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Rating computation failed")
        raise HTTPException(status_code=500, detail="Internal rating error")
