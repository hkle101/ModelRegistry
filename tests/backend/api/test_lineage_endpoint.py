"""Tests for `backend.api.lineage` router."""

from fastapi.testclient import TestClient


def test_lineage_endpoint_returns_graph(patch_backend_deps, fake_storage_manager):
    fake_storage_manager.items["a1"] = {"artifact_id": "a1", "name": "foo", "type": "model"}

    from backend.main import app

    client = TestClient(app)
    res = client.get("/artifact/model/a1/lineage")
    assert res.status_code == 200
    body = res.json()
    assert "nodes" in body and "edges" in body
