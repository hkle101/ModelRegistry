import pytest
from cli.utils.MetadataFetcher import MetadataFetcher


def test_get_download_url_github():
    fetcher = MetadataFetcher()
    url = "https://github.com/owner/repo"
    assert (
        fetcher.get_download_url(url)
        == "https://github.com/owner/repo/archive/refs/heads/main.zip"
    )


def test_get_download_url_hf_model():
    fetcher = MetadataFetcher()
    url = "https://huggingface.co/gpt2"
    assert fetcher.get_download_url(url) == "https://huggingface.co/gpt2/resolve/main/gpt2.zip"


def test_get_download_url_hf_dataset():
    fetcher = MetadataFetcher()
    url = "https://huggingface.co/datasets/squad"
    assert fetcher.get_download_url(url) == "https://huggingface.co/datasets/squad/resolve/main/squad.zip"


def test_fetch_handles_unsupported_url(monkeypatch):
    fetcher = MetadataFetcher()
    res = fetcher.fetch("https://example.com/foo")
    assert res["artifact_type"] == "unknown"
    assert "error" in res


def test_fetch_github_error(monkeypatch):
    fetcher = MetadataFetcher()
    # Force _fetch_metadata to return error
    monkeypatch.setattr(fetcher, "_fetch_metadata", lambda api_url: {"error": "boom"})
    res = fetcher.fetch("https://github.com/owner/repo")
    assert res["artifact_type"] == "code"
    assert res.get("error") == "boom"
