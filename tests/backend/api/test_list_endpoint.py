"""Tests for `backend.api.list` router."""

from fastapi.testclient import TestClient


def test_list_endpoint_returns_array(patch_backend_deps, fake_storage_manager):
    # Seed in-memory storage with one item.
    fake_storage_manager.items["a1"] = {
        "artifact_id": "a1",
        "name": "foo",
        "type": "model",
        "artifact_type": "model",
        "url": "s3://b/x",
        "download_url": "https://example.com",
    }

    from backend.main import app

    client = TestClient(app)
    res = client.post("/artifacts", json=[{"name": "*"}])
    assert res.status_code == 200
    assert isinstance(res.json(), list)
