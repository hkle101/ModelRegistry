"""S3 service wrapper.

Handles low-level S3 operations (upload/download/delete/presign/reset).
"""

import logging
from io import BytesIO
from aws.config import s3, BUCKET_NAME

logger = logging.getLogger(__name__)


class S3Service:
    """
    Handles S3 operations for storing artifact files.
    Supports uploading (from bytes), downloading, deleting, updating, and resetting the bucket.
    """

    def __init__(self, bucket_name: str = BUCKET_NAME):
        self.s3 = s3
        self.bucket_name = bucket_name

    # ------------------------
    # Helpers
    # ------------------------
    def _s3_uri(self, key: str) -> str:
        """Return a full s3:// URI."""
        return f"s3://{self.bucket_name}/{key}"

    # ------------------------
    # Artifact Operations
    # ------------------------
    def upload_artifact(self, artifact_bytes: bytes, artifact_id: str, filename: str) -> str:
        """
        Upload artifact content to S3 from bytes (in-memory).
        Returns the S3 URI.
        """
        key = f"artifacts/{artifact_id}/{filename}"
        try:
            file_obj = BytesIO(artifact_bytes)
            self.s3.upload_fileobj(file_obj, self.bucket_name, key)
            uri = self._s3_uri(key)
            logger.info(f"✅ Uploaded artifact '{filename}' to {uri}")
            return uri
        except Exception as e:
            logger.exception(f"❌ Failed to upload artifact '{filename}' for artifact_id={artifact_id}: {e}")
            raise

    def download_artifact(self, s3_key: str) -> bytes:
        """
        Download an artifact from S3 and return its content as bytes.
        """
        try:
            file_obj = BytesIO()
            self.s3.download_fileobj(self.bucket_name, s3_key, file_obj)
            file_obj.seek(0)
            logger.info(f"⬇️ Downloaded artifact '{s3_key}' from S3")
            return file_obj.read()
        except Exception as e:
            logger.exception(f"❌ Failed to download artifact '{s3_key}': {e}")
            raise

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for downloading an artifact from S3.
        """
        try:
            url = self.s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except Exception as e:
            logger.exception(f"❌ Failed to generate presigned URL for {key}: {e}")
            raise

    def delete_artifact(self, s3_key: str) -> bool:
        """
        Delete a single artifact from S3.
        Returns True if deleted successfully.
        """
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"🗑️ Deleted artifact '{s3_key}' from S3")
            return True
        except Exception as e:
            logger.exception(f"❌ Failed to delete artifact '{s3_key}': {e}")
            return False

    def reset_bucket(self) -> None:
        """
        Delete all objects in the S3 bucket.
        """
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket_name)
            if "Contents" in response:
                to_delete = [{"Key": obj["Key"]} for obj in response["Contents"]]
                self.s3.delete_objects(Bucket=self.bucket_name, Delete={"Objects": to_delete})
                logger.warning(f"⚠️ Reset S3 bucket '{self.bucket_name}'; all objects deleted")
            else:
                logger.info(f"ℹ️ S3 bucket '{self.bucket_name}' is already empty; nothing to reset")
        except Exception as e:
            logger.exception(f"❌ Failed to reset S3 bucket '{self.bucket_name}': {e}")
            raise
