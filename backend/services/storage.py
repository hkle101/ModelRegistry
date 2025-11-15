import logging
import requests
import json
from datetime import datetime
from backend.services.s3_service import S3Service
from backend.services.dynamodb_service import DynamoDBService
from cli.utils.ArtifactManager import ArtifactManager
from decimal import Decimal
from typing import Any, Dict

logger = logging.getLogger(__name__)


class StorageManager:
    """High-level storage interface for managing artifacts across S3 and DynamoDB."""

    def __init__(self):
        self.s3 = S3Service()
        self.db = DynamoDBService()
        self.artifact_manager = ArtifactManager()

    # ------------------------
    # Artifact Operations
    # ------------------------
    def create_metadata(self, artifact_data: Dict[str, Any], artifact_bytes: bytes, filename: str) -> Dict[str, Any]:
        try:
            artifact_id = artifact_data.get("artifact_id")
            if not artifact_id:
                raise ValueError("artifact_data must contain 'artifact_id'")

            # Upload artifact to S3
            s3_uri = self.s3.upload_artifact(artifact_bytes, artifact_id, filename)

            now = datetime.now().isoformat() + "Z"

            metadata = {
                "artifact_id": artifact_id,
                "name": artifact_data.get("name"),
                "type": artifact_data.get("artifact_type"),
                "license": artifact_data.get("license"),
                "size_mb": artifact_data.get("size_mb"),
                "scores": self._convert_floats_to_decimal(artifact_data.get("scores", {})),
                "related_artifacts": artifact_data.get("related_artifacts", {}),
                "metadata": artifact_data.get("metadata", {}),
                "created_at": now,
                "updated_at": now,
                "url": s3_uri,
            }

            logger.info(f"📦 Created metadata for artifact '{metadata['name']}' ({artifact_id})")
            return metadata

        except Exception:
            logger.exception(f"❌ Failed to create metadata for artifact '{artifact_data.get('name')}'")
            raise

    def store_artifact(self, artifact_data: Dict[str, Any], artifact_bytes: bytes, filename: str) -> bool:
        try:
            metadata = self.create_metadata(artifact_data, artifact_bytes, filename)
            success = self.db.create_item(metadata)
            if success:
                logger.info(f"✅ Stored artifact '{metadata['name']}' ({metadata['artifact_id']})")
            else:
                logger.error(f"❌ Failed to store artifact '{metadata['name']}' ({metadata['artifact_id']})")
            return success
        except Exception:
            logger.exception(f"❌ Exception storing artifact '{artifact_data.get('name')}'")
            return False

    def get_artifact(self, artifact_id: str) -> Dict[str, Any] | None:
        try:
            item = self.db.get_item(artifact_id)
            if not item:
                logger.warning(f"⚠️ No artifact found with artifact_id={artifact_id}")
            return item
        except Exception:
            logger.exception(f"❌ Exception retrieving artifact with artifact_id={artifact_id}")
            return None

    def delete_artifact(self, artifact_id: str) -> bool:
        try:
            item = self.db.get_item(artifact_id)
            if not item:
                logger.warning(f"⚠️ No artifact found with artifact_id={artifact_id}")
                return False

            s3_key = item.get("url", "").replace(f"s3://{self.s3.bucket_name}/", "")
            s3_deleted = False
            db_deleted = False

            try:
                s3_deleted = self.s3.delete_artifact(s3_key)
            except Exception:
                logger.exception(f"❌ Failed to delete artifact bytes from S3 for artifact_id={artifact_id}")

            try:
                db_deleted = self.db.delete_item(artifact_id)
            except Exception:
                logger.exception(f"❌ Failed to delete artifact metadata from DB for artifact_id={artifact_id}")

            if s3_deleted and db_deleted:
                logger.info(f"🗑️ Deleted artifact '{item.get('name')}' ({artifact_id})")
            else:
                logger.error(f"❌ Failed to completely delete artifact '{item.get('name')}' ({artifact_id})")

            return s3_deleted and db_deleted

        except Exception:
            logger.exception(f"❌ Exception deleting artifact with artifact_id={artifact_id}")
            return False

    def update_artifact(self, artifact_data: Dict[str, Any], artifact_bytes: bytes, filename: str) -> bool:
        try:
            artifact_id = artifact_data.get("artifact_id")
            if not artifact_id:
                raise ValueError("artifact_data must contain 'artifact_id'")

            existing_item = self.db.get_item(artifact_id)
            if not existing_item:
                logger.error(f"❌ Cannot update. No artifact found with artifact_id={artifact_id}")
                return False

            # Overwrite artifact in S3
            s3_uri = self.s3.upload_artifact(artifact_bytes, artifact_id, filename)

            # Update metadata in DynamoDB
            update_data = {
                "name": artifact_data.get("name"),
                "type": artifact_data.get("artifact_type"),
                "license": artifact_data.get("license"),
                "size_mb": artifact_data.get("size_mb"),
                "scores": self._convert_floats_to_decimal(artifact_data.get("scores", {})),
                "related_artifacts": artifact_data.get("related_artifacts", {}),
                "metadata": artifact_data.get("metadata", {}),
                "updated_at": datetime.now().isoformat() + "Z",
                "url": s3_uri,
            }

            success = self.db.update_item(artifact_id, update_data)
            if success:
                logger.info(f"✏️ Updated artifact '{artifact_data.get('name')}' ({artifact_id})")
            else:
                logger.error(f"❌ Failed to update artifact '{artifact_data.get('name')}' ({artifact_id})")
            return success

        except Exception:
            logger.exception(f"❌ Exception updating artifact '{artifact_data.get('name')}'")
            return False

    def list_artifacts(self) -> list:
        try:
            artifacts = self.db.scan_all()
            logger.info(f"📄 Retrieved list of {len(artifacts)} artifacts")
            return artifacts
        except Exception:
            logger.exception("❌ Exception listing artifacts")
            return []

    def get_artifact_bytes(self, url: str) -> bytes | None:
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            artifact_bytes = response.content
            logger.info(f"⬇️ Fetched artifact bytes from URL: {url}")
            return artifact_bytes
        except requests.RequestException:
            logger.exception(f"❌ Failed to fetch artifact bytes from URL: {url}")
            return None

    def reset(self) -> bool:
        try:
            self.s3.reset_bucket()
            logger.info("✅ S3 bucket reset successfully")
            self.db.reset_table()
            logger.info("✅ DynamoDB table reset successfully")
            logger.info("⚡ Storage reset completed successfully")
            return True
        except Exception as e:
            logger.exception(f"❌ Failed to reset storage: {e}")
            return False

    # ------------------------
    # Helpers
    # ------------------------
    @staticmethod
    def _convert_floats_to_decimal(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: StorageManager._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [StorageManager._convert_floats_to_decimal(v) for v in obj]
        elif isinstance(obj, float):
            return Decimal(str(obj))
        else:
            return obj

    # ------------------------
    # Command-line Interface
    # ------------------------
    def main(self):
        menu = """
StorageManager CLI:
1. List Artifacts
2. Get Artifact by ID
3. Upload Artifact from URL
4. Update Artifact by ID
5. Delete Artifact by ID
6. Reset Storage
7. Exit
"""

        while True:
            print(menu)
            choice = input("Enter your choice (1-7): ").strip()

            if choice == "1":
                artifacts = self.list_artifacts()
                print(json.dumps(artifacts, indent=2))

            elif choice == "2":
                artifact_id = input("Enter artifact ID: ").strip()
                artifact = self.get_artifact(artifact_id)
                if artifact:
                    print(json.dumps(artifact, indent=2))
                else:
                    print("❌ Not found")

            elif choice == "3":
                url = input("Enter artifact URL: ").strip()
                artifact_data = self.artifact_manager.processUrl(url)
                artifact_bytes = json.dumps({
                    "artifact_id": artifact_data["artifact_id"],
                    "name": artifact_data.get("name", "unnamed"),
                    "dummy_score": 42
                }, indent=2).encode("utf-8")
                filename = artifact_data.get("name", artifact_data["artifact_id"])
                success = self.store_artifact(artifact_data, artifact_bytes, filename)
                print("✅ Uploaded" if success else "❌ Upload failed")

            elif choice == "4":
                artifact_id = input("Enter artifact ID to update: ").strip()
                url = input("Enter new artifact URL: ").strip()
                artifact_data = self.artifact_manager.processUrl(url)
                artifact_data["artifact_id"] = artifact_id
                artifact_bytes = json.dumps({
                    "artifact_id": artifact_id,
                    "name": artifact_data.get("name", "unnamed"),
                    "dummy_score": 42
                }, indent=2).encode("utf-8")
                filename = artifact_data.get("name", artifact_id)
                success = self.update_artifact(artifact_data, artifact_bytes, filename)
                print("✅ Updated" if success else "❌ Update failed")

            elif choice == "5":
                artifact_id = input("Enter artifact ID to delete: ").strip()
                success = self.delete_artifact(artifact_id)
                print("✅ Deleted" if success else "❌ Delete failed")

            elif choice == "6":
                confirm = input("Are you sure you want to reset storage? (yes/no): ").strip().lower()
                if confirm == "yes":
                    success = self.reset()
                    print("✅ Storage reset" if success else "❌ Reset failed")

            elif choice == "7":
                print("Exiting CLI.")
                break

            else:
                print("Invalid choice. Please enter a number from 1-7.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager = StorageManager()
    manager.main()


