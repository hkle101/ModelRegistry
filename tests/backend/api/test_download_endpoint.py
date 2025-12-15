"""Tests for `backend.api.download` router."""

from fastapi.testclient import TestClient


def test_download_endpoint_redirects(patch_backend_deps, fake_storage_manager):
    fake_storage_manager.items["a1"] = {"artifact_id": "a1", "name": "foo", "type": "model"}

    from backend.main import app

    client = TestClient(app)
    res = client.get("/artifact/a1/download", follow_redirects=False)
    assert res.status_code == 302
    assert res.headers["location"].startswith("https://")
