# storage.py
import logging
from datetime import datetime
from botocore.exceptions import ClientError
from aws.config import s3, table, BUCKET_NAME
from typing import Dict

# --- Logging setup ---
logger = logging.getLogger("storage")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


# --- UPLOAD ARTIFACT ---
def upload_artifact(artifact_data: Dict[str, any]):
    """Upload artifact file to S3 and store metadata in DynamoDB."""
    try:
        key = f"artifacts/{artifact_data.get('id', '')}/{artifact_data.get('artifact_type', 'unknown')}.zip"
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=artifact_data)
        s3_uri = f"s3://{BUCKET_NAME}/{key}"
        logger.info(f"Uploaded artifact to S3: {s3_uri}")

        now = datetime.now().isoformat() + "Z"
        item = {
            "artifact_id": artifact_data.get("id", ""),
            "name": artifact_data.get("name", "unknown"),
            "type": artifact_data.get("artifact_type", "unknown"),
            "license": artifact_data.get("license", "unknown"),
            "size_mb": artifact_data.get("size_mb", 0),
            "ratings": artifact_data.get("scores", {}),
            "related_artifacts": artifact_data.get("related_artifacts", []),
            "created_at": now,
            "updated_at": now,
            "url": s3_uri,
        }
        table.put_item(Item=item)
        logger.info(f"Stored artifact metadata in DynamoDB: {artifact_data.get('id', '')}")
    except ClientError as e:
        logger.error(f"Failed to upload artifact {artifact_data.get('id', '')}: {e}")
        return {"error": str(e)}


# --- GET SINGLE ARTIFACT ---
def get_artifact_by_type_and_id(artifact_type, artifact_id):
    try:
        response = table.get_item(Key={"artifact_id": artifact_id})
        item = response.get("Item")
        if not item or item.get("type") != artifact_type:
            logger.warning(f"Artifact not found: type={artifact_type}, id={artifact_id}")
            return None
        return item
    except ClientError as e:
        logger.error(f"Failed to get artifact {artifact_id}: {e}")
        return {"error": str(e)}


# --- UPDATE ARTIFACT ---
def update_artifact(artifact_id, updates: dict):
    try:
        updates["updated_at"] = datetime.now().isoformat() + "Z"
        update_expr = "SET " + ", ".join(f"#{k}=:{k}" for k in updates)
        expr_attr_names = {f"#{k}": k for k in updates}
        expr_attr_values = {f":{k}": v for k, v in updates.items()}
        table.update_item(
            Key={"artifact_id": artifact_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
        )
        logger.info(f"Updated artifact {artifact_id} metadata")
        return True
    except ClientError as e:
        logger.error(f"Failed to update artifact {artifact_id}: {e}")
        return False


# --- DELETE ARTIFACT ---
def delete_artifact(artifact_id):
    try:
        item = table.get_item(Key={"artifact_id": artifact_id}).get("Item")
        if not item:
            logger.warning(f"No artifact found to delete: {artifact_id}")
            return False

        key = item["url"].split(f"{BUCKET_NAME}/")[-1]
        s3.delete_object(Bucket=BUCKET_NAME, Key=key)
        table.delete_item(Key={"artifact_id": artifact_id})
        logger.info(f"Deleted artifact {artifact_id}")
        return True

    except ClientError as e:
        logger.error(f"Failed to delete artifact {artifact_id}: {e}")
        return False


# --- LIST ARTIFACTS WITH PAGINATION ---
def list_artifacts(limit=10, offset=0):
    try:
        response = table.scan()
        items = response.get("Items", [])
        return items[offset:offset + limit]
    except ClientError as e:
        logger.error(f"Failed to list artifacts: {e}")
        return []


# --- SEARCH ARTIFACTS ---
def search_artifacts(query, limit=10, offset=0):
    try:
        response = table.scan()
        items = response.get("Items", [])
        filtered = [
            item for item in items
            if query.lower() in item.get("name", "").lower()
            or query.lower() in item.get("type", "").lower()
        ]
        return filtered[offset:offset + limit]
    except ClientError as e:
        logger.error(f"Failed to search artifacts: {e}")
        return []
    

# --- RESET STORAGE ---
def reset_storage(confirm: bool = False):
    """
    Delete all artifacts from S3 and metadata from DynamoDB.
    WARNING: Destructive operation. Pass confirm=True to proceed.
    """
    if not confirm:
        logger.warning("Reset not confirmed. Pass confirm=True to proceed.")
        return "Reset not confirmed. Pass confirm=True to proceed."

    try:
        # --- Delete all S3 objects under 'artifacts/' ---
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix="artifacts/")
        if "Contents" in response:
            deleted_s3_count = 0
            for obj in response["Contents"]:
                s3.delete_object(Bucket=BUCKET_NAME, Key=obj["Key"])
                deleted_s3_count += 1
            logger.info(f"Deleted {deleted_s3_count} objects from S3.")
        else:
            deleted_s3_count = 0
            logger.info("No S3 objects to delete.")

        # --- Delete all items in DynamoDB table ---
        response = table.scan()
        items = response.get("Items", [])
        deleted_db_count = 0
        for item in items:
            table.delete_item(Key={"artifact_id": item["artifact_id"]})
            deleted_db_count += 1
        logger.info(f"Deleted {deleted_db_count} items from DynamoDB.")

        return f"Reset complete. S3 deleted: {deleted_s3_count}, DynamoDB deleted: {deleted_db_count}"

    except Exception as e:
        logger.error(f"Failed to reset storage: {e}")
        return {"error": str(e)}

