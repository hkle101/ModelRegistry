import logging
import requests
from typing import Optional, Any, Dict, List
from datetime import datetime
from backend.services.s3_service import S3Service
from aws.config import BUCKET_NAME
from backend.services.dynamodb_service import DynamoDBService
from cli.utils.ArtifactManager import ArtifactManager

logger = logging.getLogger(__name__)


class StorageManager:
    """High-level storage interface for managing artifacts across S3 and DynamoDB."""

    def __init__(self):
        self.s3 = S3Service()
        self.db = DynamoDBService()
        self.artifact_manager = ArtifactManager()
        self.bucket_name = BUCKET_NAME

    # ------------------------
    # Artifact Operations
    # ------------------------
    def create_metadata(self, artifact_data: Dict[str, Any], artifact_bytes: bytes, filename: str) -> Dict[str, Any]:
        try:
            artifact_id = artifact_data.get("artifact_id")
            if not artifact_id:
                raise ValueError("artifact_data must contain 'artifact_id'")
            filename = artifact_data.get('name') if not filename else filename
            # Upload artifact to S3
            s3_uri = self.s3.upload_artifact(artifact_bytes, artifact_id, filename)

            now = datetime.now().isoformat() + "Z"

            metadata = {
                "artifact_id": artifact_id,
                "name": artifact_data.get("name"),
                "type": artifact_data.get("artifact_type"),
                "license": artifact_data.get("license"),
                "size_mb": artifact_data.get("size_mb"),
                "scores": (artifact_data.get("scores", {})),
                "related_artifacts": artifact_data.get("related_artifacts", {}),
                "metadata": artifact_data.get("metadata", {}),
                "created_at": now,
                "updated_at": now,
                "processed_url": artifact_data.get("processed_url", ""),
                "url": s3_uri,
            }

            logger.info(f"📦 Created metadata for artifact '{metadata['name']}' ({artifact_id})")
            return metadata

        except Exception:
            logger.exception(f"❌ Failed to create metadata for artifact '{artifact_data.get('name')}'")
            raise

    def generate_download_url(self, artifact_id: str, filename: str, expires_in: int = 3600) -> str:
        key = f"artifacts/{artifact_id}/{filename}"
        try:
            url = self.s3.generate_presigned_url(key, expires_in)
            logger.info(f"Generated presigned URL for artifact_id={artifact_id}")
            return url
        except Exception as e:
            logger.exception(f"Failed to generate presigned URL for {key}: {e}")
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

    def list_artifacts(self, queries=None, offset: Optional[int] = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Returns a paginated list of artifacts, optionally filtered by queries.
        - queries: list of ArtifactQuery dicts or objects
        - offset: number of artifacts to skip (pagination)
        - limit: number of artifacts to return
        """
        try:
            all_items = self.db.scan_all()

            # ------------------------
            # Filter artifacts if queries provided
            # ------------------------
            if queries:
                normalized = []
                for query in queries:
                    # Extract query fields
                    if isinstance(query, dict):
                        q_name = query.get("name")
                        q_types = query.get("types")
                    else:
                        q_name = getattr(query, "name", None)
                        q_types = getattr(query, "types", None)

                    # Wildcard: return all items immediately
                    if q_name == "*":
                        break

                    # Clean name and types
                    has_name = bool(q_name and q_name.strip() and q_name.strip().lower() != "string")
                    clean_types = [t.strip().lower() for t in (q_types or []) if t and t.strip().lower() != "string"]
                    has_types = bool(clean_types)

                    if has_name or has_types:
                        normalized.append({
                            "name": q_name.strip().lower() if has_name else None,
                            "types": clean_types,
                        })

                # Apply filtering only if we have meaningful constraints
                if normalized:
                    filtered = []
                    for nq in normalized:
                        q_name = nq["name"]
                        q_types = nq["types"]

                        for item in all_items:
                            item_name = (item.get("name") or "").lower()
                            item_type = (item.get("type") or item.get("artifact_type") or "").lower()

                            if q_name and q_name not in item_name:
                                continue
                            if q_types and item_type not in q_types:
                                continue
                            filtered.append(item)

                    # De-duplicate
                    seen = set()
                    deduped = []
                    for it in filtered:
                        aid = it.get("artifact_id") or it.get("id")
                        key = aid or (it.get("name"), it.get("type"))
                        if key in seen:
                            continue
                        seen.add(key)
                        deduped.append(it)

                    all_items = deduped

            # ------------------------
            # Apply pagination using offset & limit
            # ------------------------
            offset = offset or 0
            paginated = all_items[offset:offset + limit]

            # ------------------------
            # Return only metadata fields as per API spec
            # ------------------------
            results = [{
                "name": item.get("name"),
                "id": item.get("artifact_id"),
                "type": item.get("type") or item.get("artifact_type")
            } for item in paginated]

            logger.info(f"📄 Retrieved list of {len(results)} artifacts (offset={offset}, limit={limit})")
            return results

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
            logger.exception(
                f"❌ Failed to fetch artifact bytes from URL: {url}"
            )
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