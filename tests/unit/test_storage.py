import pytest
from unittest.mock import MagicMock, patch
from backend.services.storage import StorageManager


@pytest.fixture
def mock_s3():
    mock = MagicMock()
    mock.upload_artifact = MagicMock(return_value="s3://test-bucket/artifacts/123/file.zip")
    mock.update_artifact = MagicMock(return_value="s3://test-bucket/artifacts/123/file.zip")
    mock.delete_artifact = MagicMock(return_value=True)
    mock.reset_bucket = MagicMock()
    return mock


@pytest.fixture
def mock_db():
    mock = MagicMock()
    mock.create_item = MagicMock(return_value=True)
    mock.get_item = MagicMock(return_value={"artifact_id": "123", "name": "Test"})
    mock.update_item = MagicMock(return_value=True)
    mock.delete_item = MagicMock(return_value=True)
    mock.scan_all = MagicMock(return_value=[{"artifact_id": "123"}])
    mock.reset_table = MagicMock()
    return mock


@pytest.fixture
def storage_manager(mock_s3, mock_db):
    """StorageManager instance with mocked S3 and DynamoDB."""
    manager = StorageManager()
    manager.s3 = mock_s3
    manager.db = mock_db
    return manager


class TestStorageManager:

    def test_create_metadata(self, storage_manager):
        artifact_data = {"artifact_id": "123", "name": "Test", "type": "model"}
        artifact_bytes = b"dummy bytes"
        metadata = storage_manager.create_metadata(artifact_data, artifact_bytes, "file.zip")

        assert metadata["artifact_id"] == "123"
        assert metadata["name"] == "Test"
        assert metadata["url"] == "s3://test-bucket/artifacts/123/file.zip"
        storage_manager.s3.upload_artifact.assert_called_once_with(artifact_bytes, "123", "file.zip")

    def test_store_artifact_success(self, storage_manager):
        artifact_data = {"artifact_id": "123", "name": "Test", "type": "model"}
        artifact_bytes = b"dummy bytes"
        result = storage_manager.store_artifact(artifact_data, artifact_bytes, "file.zip")
        assert result is True
        storage_manager.db.create_item.assert_called_once()

    def test_get_artifact_found(self, storage_manager):
        artifact = storage_manager.get_artifact("123")
        assert artifact["artifact_id"] == "123"

    def test_delete_artifact_success(self, storage_manager):
        result = storage_manager.delete_artifact("123")
        assert result is True
        storage_manager.s3.delete_artifact.assert_called_once()
        storage_manager.db.delete_item.assert_called_once()

    def test_update_artifact_success(self, storage_manager):
        artifact_data = {"artifact_id": "123", "name": "Test", "type": "model"}
        artifact_bytes = b"updated bytes"
        result = storage_manager.update_artifact(artifact_data, artifact_bytes, "file.zip")
        assert result is True
        storage_manager.s3.update_artifact.assert_called_once()
        storage_manager.db.update_item.assert_called_once()

    def test_list_artifacts(self, storage_manager):
        artifacts = storage_manager.list_artifacts()
        assert len(artifacts) == 1
        assert artifacts[0]["artifact_id"] == "123"

    def test_get_artifact_bytes_success(self, storage_manager):
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"artifact content"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = storage_manager.get_artifact_bytes("http://example.com/file.zip")
            assert result == b"artifact content"

    def test_reset_storage(self, storage_manager):
        result = storage_manager.reset()
        assert result is True
        storage_manager.s3.reset_bucket.assert_called_once()
        storage_manager.db.reset_table.assert_called_once()
