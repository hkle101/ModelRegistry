import pytest
import requests_mock
from cli.utils.MetadataFetcher import MetadataFetcher


@pytest.fixture
def mock_fetcher():
    """Fixture for MetadataFetcher with no token."""
    return MetadataFetcher(github_token=None)


def test_fetch_hf_model_metadata(mock_fetcher):
    url = "https://huggingface.co/gpt2"
    api_url = "https://huggingface.co/api/models/gpt2"

    with requests_mock.Mocker() as m:
        m.get(api_url, json={"modelId": "gpt2", "downloads": 1000}, status_code=200)
        result = mock_fetcher.fetch(url)

    assert result["artifact_type"] == "model"
    assert "modelId" in result


def test_fetch_hf_dataset_metadata(mock_fetcher):
    url = "https://huggingface.co/datasets/squad"
    api_url = "https://huggingface.co/api/datasets/squad"

    with requests_mock.Mocker() as m:
        m.get(api_url, json={"datasetId": "squad"}, status_code=200)
        result = mock_fetcher.fetch(url)

    assert result["artifact_type"] == "dataset"
    assert result["datasetId"] == "squad"


def test_fetch_github_metadata(mock_fetcher):
    url = "https://github.com/owner/repo"
    api_url = "https://api.github.com/repos/owner/repo"

    with requests_mock.Mocker() as m:
        m.get(api_url, json={"full_name": "owner/repo"}, status_code=200)
        result = mock_fetcher.fetch(url)

    assert result["artifact_type"] == "code"
    assert result["full_name"] == "owner/repo"


def test_fetch_unsupported_url(mock_fetcher):
    url = "https://example.com/unknown"
    result = mock_fetcher.fetch(url)

    assert result["artifact_type"] == "unknown"
    assert "error" in result


def test_fetch_handles_http_error(mock_fetcher):
    """Simulate an API error gracefully handled."""
    url = "https://huggingface.co/gpt2"
    api_url = "https://huggingface.co/api/models/gpt2"

    with requests_mock.Mocker() as m:
        m.get(api_url, status_code=404, json={"message": "Not found"})
        result = mock_fetcher.fetch(url)

    assert result["artifact_type"] == "model"
    assert "error" in result


def test_fetch_handles_invalid_github_url(mock_fetcher):
    """Simulate GitHub URL that doesn't match expected pattern."""
    url = "https://github.com/invalid"
    result = mock_fetcher.fetch(url)

    assert result["artifact_type"] == "unknown"
    assert "error" in result
