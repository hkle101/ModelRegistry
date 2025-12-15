"""Tests for `backend.api.update` router."""

from fastapi.testclient import TestClient


def test_update_endpoint_returns_ack(patch_backend_deps):
    from backend.main import app

    client = TestClient(app)
    res = client.put("/artifacts/model/a1", json={"x": 1})
    assert res.status_code == 200
    assert res.json()["artifact_id"] == "a1"
