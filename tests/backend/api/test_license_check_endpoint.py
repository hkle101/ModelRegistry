"""Tests for `backend.api.license_check` router."""

import pytest
from fastapi.testclient import TestClient


class _Resp:
    """Tiny requests-like response stub for patching external HTTP calls."""

    def __init__(self, status_code=200):
        self.status_code = status_code


def test_license_check_endpoint_returns_true(monkeypatch: pytest.MonkeyPatch, patch_backend_deps, fake_storage_manager):
    fake_storage_manager.items["a1"] = {"artifact_id": "a1", "name": "foo", "type": "model"}

    monkeypatch.setattr(
        "backend.api.license_check.requests.head",
        lambda *args, **kwargs: _Resp(status_code=200),
    )

    from backend.main import app

    client = TestClient(app)
    res = client.post("/artifact/model/a1/license-check", json={"github_url": "https://github.com/o/r"})
    assert res.status_code == 200
    assert res.json() is True
