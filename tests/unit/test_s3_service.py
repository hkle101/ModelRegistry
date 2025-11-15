import pytest
from unittest.mock import MagicMock, ANY
from backend.services.s3_service import S3Service  # import service class


@pytest.fixture
def mock_s3():
    """Fixture that mocks boto3 S3 client methods."""
    mock = MagicMock()
    mock.upload_fileobj = MagicMock()
    mock.download_fileobj = MagicMock()
    mock.delete_object = MagicMock()
    mock.list_objects_v2 = MagicMock()
    mock.delete_objects = MagicMock()
    return mock


@pytest.fixture
def s3_service(mock_s3):
    """Fixture providing an S3Service instance with mocked client."""
    service = S3Service(bucket_name="test-bucket")
    service.s3 = mock_s3
    return service


class TestS3Service:
    """Unit tests for S3Service."""

    def test_s3_uri(self, s3_service):
        uri = s3_service._s3_uri("artifacts/key")
        assert uri == "s3://test-bucket/artifacts/key"

    def test_upload_artifact_success(self, s3_service):
        data = b"test-bytes"
        uri = s3_service.upload_artifact(data, "123", "model.zip")

        # Check method calls
        s3_service.s3.upload_fileobj.assert_called_once()
        assert uri == "s3://test-bucket/artifacts/123/model.zip"

    def test_upload_artifact_failure(self, s3_service):
        s3_service.s3.upload_fileobj.side_effect = Exception("Upload failed")

        with pytest.raises(Exception, match="Upload failed"):
            s3_service.upload_artifact(b"abc", "123", "broken.zip")

    def test_download_artifact_success(self, s3_service):
        test_bytes = b"downloaded content"

        # Mock S3 download_fileobj to write bytes into file_obj
        def mock_download(_bucket, _key, file_obj):
            file_obj.write(test_bytes)

        s3_service.s3.download_fileobj.side_effect = mock_download

        # Call the method
        result = s3_service.download_artifact("artifacts/123/model.zip")

        # Assert download_fileobj was called correctly
        s3_service.s3.download_fileobj.assert_called_once_with(
            "test-bucket", "artifacts/123/model.zip", ANY
        )

        # Assert the bytes returned are correct
        assert result == test_bytes

    def test_delete_artifact_success(self, s3_service):
        s3_service.s3.delete_object.return_value = {}
        result = s3_service.delete_artifact("artifacts/123/model.zip")

        s3_service.s3.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key="artifacts/123/model.zip"
        )
        assert result is True

    def test_delete_artifact_failure(self, s3_service):
        s3_service.s3.delete_object.side_effect = Exception("Delete failed")
        result = s3_service.delete_artifact("bad/key")
        assert result is False

    def test_update_artifact_success(self, s3_service):
        data = b"new content"
        uri = s3_service.update_artifact(data, "123", "model.zip")

        s3_service.s3.upload_fileobj.assert_called_once()
        assert uri == "s3://test-bucket/artifacts/123/model.zip"

    def test_reset_bucket_with_contents(self, s3_service):
        s3_service.s3.list_objects_v2.return_value = {
            "Contents": [{"Key": "a"}, {"Key": "b"}]
        }

        s3_service.reset_bucket()

        s3_service.s3.list_objects_v2.assert_called_once_with(
            Bucket="test-bucket"
        )
        s3_service.s3.delete_objects.assert_called_once_with(
            Bucket="test-bucket",
            Delete={"Objects": [{"Key": "a"}, {"Key": "b"}]},
        )

    def test_reset_bucket_empty(self, s3_service):
        s3_service.s3.list_objects_v2.return_value = {}

        s3_service.reset_bucket()

        s3_service.s3.list_objects_v2.assert_called_once_with(
            Bucket="test-bucket"
        )
        s3_service.s3.delete_objects.assert_not_called()
