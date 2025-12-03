import logging
import requests
import re
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
        """
        Uploads artifact bytes to S3, generates metadata dictionary, and returns it.
        """
        try:
            artifact_id = artifact_data.get("artifact_id")
            if not artifact_id:
                raise ValueError("artifact_data must contain 'artifact_id'")
            filename = artifact_data.get('name') if not filename else filename
            s3_uri = self.s3.upload_artifact(artifact_bytes, artifact_id, filename)
            now = datetime.utcnow().isoformat() + "Z"

            metadata = {
                "artifact_id": artifact_id,
                "name": artifact_data.get("name"),
                "type": artifact_data.get("artifact_type"),
                "license": artifact_data.get("license"),
                "size_mb": artifact_data.get("size_mb"),
                "scores": artifact_data.get("scores", {}),
                "related_artifacts": artifact_data.get("related_artifacts", {}),
                "metadata": artifact_data.get("metadata", {}),
                "created_at": now,
                "updated_at": now,
                "processed_url": artifact_data.get("processed_url", ""),
                "url": s3_uri,
                "download_url": artifact_data.get("download_url", ""),
            }

            logger.info(f"📦 Created metadata for artifact '{metadata['name']}' ({artifact_id})")
            return metadata

        except Exception:
            logger.exception(f"❌ Failed to create metadata for artifact '{artifact_data.get('name')}'")
            raise

    def generate_download_url(self, artifact_id: str, filename: str, expires_in: int = 3600) -> str:
        """
        Generates a presigned S3 URL for downloading the artifact.
        """
        key = f"artifacts/{artifact_id}/{filename}"
        try:
            url = self.s3.generate_presigned_url(key, expires_in)
            logger.info(f"Generated presigned URL for artifact_id={artifact_id}")
            return url
        except Exception as e:
            logger.exception(f"Failed to generate presigned URL for {key}: {e}")
            raise

    def store_artifact(self, artifact_data: Dict[str, Any], artifact_bytes: bytes, filename: str) -> bool:
        """
        Stores the artifact bytes and metadata in S3 and DynamoDB.
        """
        try:
            metadata = self.create_metadata(artifact_data, artifact_bytes, filename)
            metadata["download_url"] = self.generate_download_url(
                metadata["artifact_id"], filename
            )
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
        """
        Retrieve artifact metadata by ID.
        """
        try:
            item = self.db.get_item(artifact_id)
            if not item:
                logger.warning(f"⚠️ No artifact found with artifact_id={artifact_id}")
            return item
        except Exception:
            logger.exception(f"❌ Exception retrieving artifact with artifact_id={artifact_id}")
            return None

    def get_artifact_bytes(self, url: str) -> bytes | None:
        """
        Fetch artifact bytes from a URL.
        """
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
        """
        Reset S3 bucket and DynamoDB table.
        """
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

    def list_artifacts(self, queries: List[Dict[str, Any]], offset: Optional[int] = 0, page_size: int = 3) -> Dict[str, Any]:
        """
        List artifacts matching provided queries with pagination.
        
        - queries: list of dicts containing filters; if name == "*", enumerate all.
                Each query may include 'types' list to filter artifact types.
        - offset: starting index for pagination.
        - page_size: number of items per page.
        
        Returns:
            dict: {"items": [artifact metadata], "next_offset": int}
        """
        try:
            all_items = self.db.scan_all()

            # Normalize queries: ensure lowercase type list
            norm_queries: List[Dict[str, Any]] = []
            for q in queries:
                name = q.get('name', '*')
                # Gather types from 'types' list or single 'type'
                if 'types' in q and isinstance(q['types'], list) and q['types']:
                    types_list = [str(t).lower() for t in q['types'] if t]
                elif 'type' in q and q.get('type'):
                    types_list = [str(q.get('type')).lower()]
                else:
                    types_list = []
                norm_queries.append({'name': name, 'types': types_list})

            def match(item: Dict[str, Any], q: Dict[str, Any]) -> bool:
                name_filter = q['name']
                name_match = True if name_filter == '*' else name_filter.lower() in str(item.get('name', '')).lower()
                stored_type = (item.get('type') or item.get('artifact_type') or '').lower()
                types_needed = q['types']
                type_match = True if not types_needed else stored_type in types_needed
                return name_match and type_match

            filtered = [item for item in all_items if any(match(item, nq) for nq in norm_queries)]

            # Pagination
            start = int(offset or 0)
            end = min(start + page_size, len(filtered))
            page = filtered[start:end]
            next_offset = end if end < len(filtered) else None

            # Minimal metadata for response
            items = []
            for it in page:
                items.append({
                    'name': it.get('name'),
                    'id': it.get('artifact_id'),
                    'type': (it.get('type') or it.get('artifact_type')),
                    'url': it.get('url'),
                    'download_url': it.get('download_url')
                })

            return {'items': items, 'next_offset': next_offset}

        except Exception:
            logger.exception("❌ Failed to list artifacts")
            raise

    def search_artifacts_by_regex(self, regex: str) -> List[Dict[str, Any]]:
        """
        Search for artifacts whose **name** or **README text** matches a regex.

        Returns a list of full artifact metadata dictionaries.
        """
        try:
            if not regex or not isinstance(regex, str):
                raise ValueError("Invalid regex")

            logger.info(f"🔍 Running regex search on artifacts: pattern={regex}")

            try:
                pattern = re.compile(regex, re.IGNORECASE)
            except re.error as e:
                logger.error(f"❌ Invalid regex pattern: {regex}")
                raise ValueError(f"Invalid regex: {e}")

            # Fetch all items (you already do this for scan_all)
            all_items = self.db.scan_all()

            matched = []
            for item in all_items:
                name = item.get("name", "")
                readme_text = item.get("metadata", {}).get("readme", "")

                # Perform regex match on both name and README
                if pattern.search(name) or pattern.search(readme_text):
                    matched.append(item)

            if len(matched) == 0:
                logger.warning(f"⚠️ No artifacts matched regex: {regex}")
                return []

            logger.info(f"✅ Regex search returned {len(matched)} artifacts")
            return matched

        except Exception:
            logger.exception(f"❌ Failed during regex artifact search (pattern={regex})")
            raise

    def delete_artifact(self, artifact_id: str) -> bool:
        """
        Delete an artifact from both S3 and DynamoDB.
        Safely handles empty strings, missing fields, and older stored formats.
        """
        try:
            # --- Fetch metadata ---
            item = self.db.get_item(artifact_id)
            if not item:
                logger.warning(f"⚠️ No artifact found with artifact_id={artifact_id}")
                return False

            name = item.get("name", "<unknown>")

            # --- Extract S3 key from stored s3://bucket/... URI ---
            raw_url = item.get("url", "")

            if raw_url.startswith("s3://"):
                # New correct format
                prefix = f"s3://{self.s3.bucket_name}/"
                s3_key = raw_url[len(prefix):]
            else:
                # Fallback for older formats (or misformatted ones)
                # example: "https://BUCKET_NAME.s3.amazonaws.com/artifacts/..."
                s3_key = raw_url.split(f"{self.s3.bucket_name}/")[-1]

            if not s3_key:
                logger.error(f"❌ Could not extract S3 key for artifact_id={artifact_id}, url={raw_url}")
                return False

            logger.info(f"🗑️ Preparing to delete artifact '{name}' ({artifact_id})")
            logger.info(f"   • S3 key resolved as: {s3_key}")

            # --- Delete object from S3 ---
            try:
                s3_deleted = self.s3.delete_artifact(s3_key)
                if s3_deleted:
                    logger.info(f"   ✔ S3 object deleted: {s3_key}")
                else:
                    logger.error(f"   ❌ Failed to delete S3 object: {s3_key}")
            except Exception:
                logger.exception(f"❌ Exception while deleting S3 object for {artifact_id}")
                s3_deleted = False

            # --- Delete metadata from DynamoDB ---
            try:
                db_deleted = self.db.delete_item(artifact_id)
                if db_deleted:
                    logger.info(f"   ✔ DynamoDB item deleted for artifact_id={artifact_id}")
                else:
                    logger.error(f"   ❌ FAILED deleting DynamoDB item for artifact_id={artifact_id}")
            except Exception:
                logger.exception(f"❌ Exception while deleting DynamoDB entry for {artifact_id}")
                db_deleted = False

            # --- Final result ---
            if s3_deleted and db_deleted:
                logger.info(f"🗑️✨ Successfully deleted artifact '{name}' ({artifact_id})")
            else:
                logger.error(
                    f"❌ Incomplete delete for artifact '{name}' ({artifact_id}). "
                    f"S3 deleted={s3_deleted}, DB deleted={db_deleted}"
                )

            return s3_deleted and db_deleted

        except Exception:
            logger.exception(f"❌ Unexpected exception while deleting artifact {artifact_id}")
            return False
