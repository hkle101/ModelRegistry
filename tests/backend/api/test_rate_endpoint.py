"""Tests for `backend.api.rate` router."""

from fastapi.testclient import TestClient


def test_rate_endpoint_returns_scores(patch_backend_deps, fake_storage_manager):
    fake_storage_manager.items["a1"] = {
        "artifact_id": "a1",
        "name": "foo",
        "type": "model",
        "artifact_type": "model",
        "scores": {"net_score": 0.5, "name": "", "category": ""},
    }

    from backend.main import app

    client = TestClient(app)
    res = client.get("/artifact/model/a1/rate")
    assert res.status_code == 200
    assert "net_score" in res.json()
