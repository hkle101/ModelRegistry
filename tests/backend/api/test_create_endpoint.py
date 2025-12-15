"""Tests for `backend.api.create` router."""

import pytest
from fastapi.testclient import TestClient


class _Resp:
    """Tiny requests-like response stub for patching external HTTP calls."""

    def __init__(self, status_code=200, content=b""):
        self.status_code = status_code
        self.content = content


def test_create_endpoint_creates_artifact(monkeypatch: pytest.MonkeyPatch, patch_backend_deps):
    monkeypatch.setattr(
        "backend.api.create.requests.get",
        lambda *args, **kwargs: _Resp(status_code=200, content=b"bytes"),
    )

    from backend.main import app

    client = TestClient(app)
    res = client.post("/artifact/model", json={"url": "https://github.com/o/r"})
    assert res.status_code == 201
    assert "metadata" in res.json()
