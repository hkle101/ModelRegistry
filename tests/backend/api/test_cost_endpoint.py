"""Tests for `backend.api.cost` router."""

from fastapi.testclient import TestClient


def test_cost_endpoint_returns_total_cost(patch_backend_deps, fake_storage_manager):
    fake_storage_manager.items["a1"] = {"artifact_id": "a1", "name": "foo", "type": "model", "size_in_gb": 1.0}

    from backend.main import app

    client = TestClient(app)
    res = client.get("/artifact/model/a1/cost")
    assert res.status_code == 200
    assert "a1" in res.json()
