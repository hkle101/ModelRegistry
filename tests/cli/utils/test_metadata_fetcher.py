import pytest

from cli.utils.MetadataFetcher import MetadataFetcher


class _Resp:
    """Minimal requests-like response stub for `MetadataFetcher` tests."""

    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("bad")

    def json(self):
        return self._payload


def test_metadata_fetcher_github(monkeypatch: pytest.MonkeyPatch):
    def fake_get(url, headers=None, timeout=10):
        assert url.startswith("https://api.github.com/repos/")
        return _Resp({"full_name": "o/r"})

    monkeypatch.setattr("cli.utils.MetadataFetcher.requests.get", fake_get)

    mf = MetadataFetcher(github_token=None)
    out = mf.fetch("https://github.com/o/r")
    assert out["artifact_type"] == "code"
    assert out["download_url"].endswith("/archive/refs/heads/main.zip")


def test_metadata_fetcher_hf_model_download_url(monkeypatch: pytest.MonkeyPatch):
    def fake_get(url, headers=None, timeout=10):
        assert url.startswith("https://huggingface.co/api/models/")
        return _Resp({"id": "org/model", "siblings": [{"rfilename": "model.safetensors"}]})

    monkeypatch.setattr("cli.utils.MetadataFetcher.requests.get", fake_get)

    mf = MetadataFetcher(github_token=None)
    out = mf.fetch("https://huggingface.co/org/model")
    assert out["artifact_type"] == "model"
    assert out["download_url"] == "https://huggingface.co/org/model/resolve/main/model.safetensors"
