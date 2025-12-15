from fastapi import APIRouter, HTTPException, Response, Body, Query
from pydantic import BaseModel
from typing import Optional, List
import logging
from backend.deps import storage_manager

router = APIRouter()
logger = logging.getLogger(__name__)

# -----------------------------
# Pydantic models
# -----------------------------


class ArtifactQuery(BaseModel):
    name: str
    types: Optional[List[str]] = None  # can be ["model", "code", "dataset"]


class ArtifactMetadata(BaseModel):
    name: str
    id: str
    type: str
    url: Optional[str] = None
    download_url: Optional[str] = None

# -----------------------------
# Endpoint
# -----------------------------


@router.post(
    "/artifacts",
    response_model=List[ArtifactMetadata],
    summary="Get the artifacts from the registry. (BASELINE)",
    description=(
        "Get artifacts fitting the query. "
        "If you want to enumerate all artifacts, provide a single query with name='*'."
    ),
)
def list_artifacts(
    response: Response,
    queries: List[ArtifactQuery] = Body(..., description="Array of ArtifactQuery"),
    offset: Optional[int] = Query(
        default=None,
        description="Provide this for pagination. Returns first page if not provided.",
    ),
):
    try:
        if not queries or len(queries) == 0:
            raise HTTPException(status_code=400, detail="Invalid or missing ArtifactQuery array")

        # Convert Pydantic objects to dicts (ensure 'types' key is a list)
        query_dicts = [
            {**q.model_dump(exclude_none=True), "types": q.types or []}
            for q in queries
        ]

        # Get artifacts from storage manager
        result = storage_manager.list_artifacts(query_dicts, offset=offset, page_size=10)
        items = result.get("items", [])
        next_offset = result.get("next_offset")

        if len(items) > 100:
            raise HTTPException(status_code=413, detail="Too many artifacts returned")

        if next_offset is not None:
            response.headers["offset"] = str(next_offset)

        return items

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to list artifacts")
        raise HTTPException(status_code=500, detail="Internal Server Error")
