"""Tests for `backend.api.byregex` router."""

from fastapi.testclient import TestClient


def test_byregex_endpoint_returns_matches(patch_backend_deps, fake_storage_manager):
    fake_storage_manager.items["a1"] = {
        "artifact_id": "a1",
        "name": "foo",
        "type": "model",
        "artifact_type": "model",
        "metadata": {"readme": "hello"},
    }

    from backend.main import app

    client = TestClient(app)
    res = client.post("/artifact/byRegEx", json={"regex": "foo"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)
