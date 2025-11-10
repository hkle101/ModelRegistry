# crud.py
from typing import List, Optional, Dict, Any
from aws.storage import (
    upload_artifact,
    get_artifact_by_type_and_id,
    update_artifact,
    delete_artifact,
    list_artifacts,
    search_artifacts,
    reset_storage
)
import logging

logger = logging.getLogger("crud")
logger.setLevel(logging.INFO)

# --------------------------
# CREATE / UPLOAD ARTIFACT
# --------------------------


def create_artifact(artifact_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upload artifact to S3 and store metadata in DynamoDB.
    """
    result = upload_artifact(artifact_data)
    if result and "error" in result:
        logger.error(f"Failed to create artifact: {result['error']}")
        raise Exception(result["error"])
    return result or {"status": "success", "artifact_id": artifact_data.get("id")}

# --------------------------
# READ / GET SINGLE ARTIFACT
# --------------------------
def read_artifact(artifact_type: str, artifact_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single artifact metadata by type and id.
    """
    result = get_artifact_by_type_and_id(artifact_type, artifact_id)
    if not result:
        logger.warning(f"Artifact not found: type={artifact_type}, id={artifact_id}")
        return None
    return result

# --------------------------
# UPDATE ARTIFACT
# --------------------------
def update_artifact_metadata(artifact_type: str, artifact_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update artifact metadata in DynamoDB.
    """
    return update_artifact(artifact_id, updates)

# --------------------------
# DELETE ARTIFACT
# --------------------------
def delete_artifact_by_id(artifact_type: str, artifact_id: str) -> bool:
    """
    Delete artifact from S3 and DynamoDB.
    """
    return delete_artifact(artifact_id)

# --------------------------
# LIST ARTIFACTS
# --------------------------
def list_all_artifacts(limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """
    List all artifacts with pagination.
    """
    return list_artifacts(limit=limit, offset=offset)

# --------------------------
# SEARCH ARTIFACTS BY NAME/TYPE
# --------------------------
def search_artifacts_by_query(query: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Search artifacts by query string (matches name or type).
    """
    return search_artifacts(query, limit=limit, offset=offset)

# --------------------------
# RESET STORAGE
# --------------------------
def reset_registry(confirm: bool = False) -> str:
    """
    Reset S3 and DynamoDB storage.
    """
    return reset_storage(confirm=confirm)
