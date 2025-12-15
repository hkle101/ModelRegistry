"""Tests for `backend.api.health` router."""

from fastapi.testclient import TestClient


def test_health_endpoint_returns_200(patch_backend_deps):
    from backend.main import app

    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
