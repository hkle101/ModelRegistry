"""Tests for `backend.api.reset` router."""

from fastapi.testclient import TestClient


def test_reset_endpoint_returns_message(patch_backend_deps):
    from backend.main import app

    client = TestClient(app)
    res = client.delete("/reset")
    assert res.status_code == 200
    assert res.json()["message"] == "Registry reset"
