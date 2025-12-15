"""Tests for `backend.api.delete` router."""

from fastapi.testclient import TestClient


def test_delete_endpoint_deletes_existing(patch_backend_deps, fake_storage_manager):
    fake_storage_manager.items["a1"] = {"artifact_id": "a1", "name": "foo", "type": "model"}

    from backend.main import app

    client = TestClient(app)
    res = client.delete("/artifacts/model/a1")
    assert res.status_code == 200
