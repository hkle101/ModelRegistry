"""DynamoDB service wrapper.

Provides CRUD + scan utilities for artifact metadata stored in DynamoDB.
"""

import logging
from typing import Optional, List, Dict, Any
from botocore.exceptions import ClientError
from aws.config import table as default_table  # rename imported table

logger = logging.getLogger(__name__)


class DynamoDBService:
    """
    Handles CRUD operations for artifact metadata in DynamoDB.
    """

    def __init__(self, table=None):
        # Use the passed table or fallback to default_table from config
        self.table = table or default_table

    # ------------------------
    # CRUD Operations
    # ------------------------
    def create_item(self, item: Dict[str, Any]) -> bool:
        try:
            self.table.put_item(Item=item)
            logger.info(f"✅ Inserted artifact (artifact_id={item.get('artifact_id')})")
            return True
        except ClientError as e:
            logger.error(f"❌ Failed to insert artifact: {e}")
            return False

    def get_item(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.table.get_item(Key={"artifact_id": artifact_id})
            item = response.get("Item")
            if item:
                logger.info(f"📦 Retrieved artifact (artifact_id={artifact_id})")
                return item
            logger.warning(f"⚠️ Artifact not found (artifact_id={artifact_id})")
            return None
        except ClientError as e:
            logger.error(f"❌ Failed to fetch artifact (artifact_id={artifact_id}): {e}")
            return None

    def update_item(self, artifact_id: str, update_data: Dict[str, Any]) -> bool:
        try:
            update_expression = "SET " + ", ".join(f"#{k}=:{k}" for k in update_data)
            expression_attr_names = {f"#{k}": k for k in update_data}
            expression_attr_values = {f":{k}": v for k, v in update_data.items()}

            self.table.update_item(
                Key={"artifact_id": artifact_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attr_names,
                ExpressionAttributeValues=expression_attr_values,
            )
            logger.info(f"✏️ Updated artifact (artifact_id={artifact_id})")
            return True
        except ClientError as e:
            logger.error(f"❌ Failed to update artifact (artifact_id={artifact_id}): {e}")
            return False

    def delete_item(self, artifact_id: str) -> bool:
        try:
            self.table.delete_item(Key={"artifact_id": artifact_id})
            logger.info(f"🗑️ Deleted artifact (artifact_id={artifact_id})")
            return True
        except ClientError as e:
            logger.error(f"❌ Failed to delete artifact (artifact_id={artifact_id}): {e}")
            return False

        # ------------------------
    # List / Scan
    # ------------------------
    def list_items(self) -> List[Dict[str, Any]]:
        """
        Return all items in the table. Alias for scan_all.
        """
        return self.scan_all()

    def scan_all(self) -> List[Dict[str, Any]]:
        try:
            response = self.table.scan()
            items = response.get("Items", [])
            logger.info(f"📜 Retrieved {len(items)} artifacts from table")
            return items
        except ClientError as e:
            logger.error(f"❌ Failed to scan artifacts table: {e}")
            return []

    def reset_table(self) -> None:
        """
        Deletes all items from the DynamoDB table.
        WARNING: This is destructive and will remove all metadata.
        """
        try:
            items = self.scan_all()
            for item in items:
                artifact_id = item.get("artifact_id")
                if artifact_id:
                    self.delete_item(artifact_id)
            logger.warning("⚠️ All artifact metadata deleted from DynamoDB.")
        except Exception as e:
            logger.exception(f"❌ Failed to reset DynamoDB table: {e}")
            raise


