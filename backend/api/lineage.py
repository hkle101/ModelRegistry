from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
import logging
from backend.deps import storage_manager, verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


class ArtifactLineageNode(BaseModel):
    artifact_id: str
    name: str
    source: str


class ArtifactLineageEdge(BaseModel):
    from_node_artifact_id: str
    to_node_artifact_id: str
    relationship: str


class ArtifactLineageGraph(BaseModel):
    nodes: List[ArtifactLineageNode]
    edges: List[ArtifactLineageEdge]


@router.get("/artifact/model/{id}/lineage", response_model=ArtifactLineageGraph)
def artifact_lineage(id: str, _: bool = Depends(verify_token)):
    try:
        artifact = storage_manager.get_artifact(id)
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")
        graph = ArtifactLineageGraph(
            nodes=[
                ArtifactLineageNode(
                    artifact_id=id,
                    name=artifact.get("name", "unknown"),
                    source="config_json",
                ),
                ArtifactLineageNode(
                    artifact_id="base-" + id,
                    name="base-model",
                    source="config_json",
                ),
            ],
            edges=[
                ArtifactLineageEdge(
                    from_node_artifact_id="base-" + id,
                    to_node_artifact_id=id,
                    relationship="base_model",
                )
            ],
        )
        return graph
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Lineage retrieval failed")
        raise HTTPException(status_code=400, detail=str(e))