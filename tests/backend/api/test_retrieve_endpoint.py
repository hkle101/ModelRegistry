"""Tests for `backend.api.retrieve` router."""

from fastapi.testclient import TestClient


def test_retrieve_endpoint_happy_path(patch_backend_deps, fake_storage_manager):
    fake_storage_manager.items["a1"] = {
        "artifact_id": "a1",
        "name": "foo",
        "type": "model",
        "artifact_type": "model",
        "processed_url": "https://github.com/o/r",
    }

    from backend.main import app

    client = TestClient(app)
    res = client.get("/artifacts/model/a1")
    assert res.status_code == 200
    assert res.json()["metadata"]["id"] == "a1"
