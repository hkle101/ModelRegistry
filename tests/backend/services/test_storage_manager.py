from __future__ import annotations

import pytest

from backend.services.storage import StorageManager


class _FakeS3:
    """In-memory S3Service-like stub used to unit test `StorageManager`."""

    def __init__(self, bucket_name="b"):
        self.bucket_name = bucket_name
        self.upload_calls = []
        self.delete_calls = []

    def upload_artifact(self, artifact_bytes: bytes, artifact_id: str, filename: str) -> str:
        self.upload_calls.append((artifact_id, filename, artifact_bytes))
        return f"s3://{self.bucket_name}/artifacts/{artifact_id}/{filename}"

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return f"https://example.com/{key}?exp={expires_in}"

    def delete_artifact(self, s3_key: str) -> bool:
        self.delete_calls.append(s3_key)
        return True

    def reset_bucket(self) -> None:
        return None


class _FakeDB:
    """In-memory DynamoDBService-like stub used to unit test `StorageManager`."""

    def __init__(self):
        self.items = {}
        self.created = []
        self.deleted = []

    def create_item(self, item):
        self.created.append(item)
        self.items[item["artifact_id"]] = dict(item)
        return True

    def get_item(self, artifact_id: str):
        return self.items.get(artifact_id)

    def delete_item(self, artifact_id: str) -> bool:
        self.deleted.append(artifact_id)
        return self.items.pop(artifact_id, None) is not None

    def scan_all(self):
        return list(self.items.values())

    def reset_table(self) -> None:
        self.items.clear()


def test_storage_manager_create_metadata_requires_artifact_id():
    sm = StorageManager()
    sm.s3 = _FakeS3()
    sm.db = _FakeDB()

    with pytest.raises(ValueError):
        sm.create_metadata({"name": "n"}, b"x", "n")


def test_storage_manager_create_metadata_uploads_and_shapes_fields():
    sm = StorageManager()
    sm.s3 = _FakeS3(bucket_name="b")
    sm.db = _FakeDB()

    md = sm.create_metadata(
        {"artifact_id": "a1", "name": "n", "artifact_type": "model", "metadata": {"readme": "hi"}},
        b"bytes",
        "n",
    )

    assert md["artifact_id"] == "a1"
    assert md["type"] == "model"
    assert md["url"].startswith("s3://b/")
    assert md["metadata"]["readme"] == "hi"


def test_storage_manager_list_artifacts_filters_name_and_type():
    sm = StorageManager()
    sm.s3 = _FakeS3()
    sm.db = _FakeDB()

    sm.db.items = {
        "a1": {"artifact_id": "a1", "name": "foo", "type": "model", "url": "u1", "download_url": "d1"},
        "a2": {"artifact_id": "a2", "name": "bar", "type": "dataset", "url": "u2", "download_url": "d2"},
    }

    out = sm.list_artifacts([{"name": "f", "types": ["model"]}], offset=0, page_size=10)
    assert [it["id"] for it in out["items"]] == ["a1"]


def test_storage_manager_search_artifacts_by_regex_invalid_pattern():
    sm = StorageManager()
    sm.s3 = _FakeS3()
    sm.db = _FakeDB()

    with pytest.raises(ValueError):
        sm.search_artifacts_by_regex("[")


def test_storage_manager_delete_artifact_parses_s3_uri_and_deletes_everywhere():
    sm = StorageManager()
    sm.s3 = _FakeS3(bucket_name="b")
    sm.db = _FakeDB()

    sm.db.items["a1"] = {
        "artifact_id": "a1",
        "name": "n",
        "url": "s3://b/artifacts/a1/n",
    }

    ok = sm.delete_artifact("a1")
    assert ok is True
    assert sm.s3.delete_calls == ["artifacts/a1/n"]
    assert sm.db.deleted == ["a1"]
