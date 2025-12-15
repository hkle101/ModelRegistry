import pytest

from backend.api.create import ArtifactUploadRequest


def test_artifact_upload_request_valid_minimal():
    m = ArtifactUploadRequest(url="https://example.com")
    assert m.url == "https://example.com"
    assert m.name is None


def test_artifact_upload_request_requires_url():
    with pytest.raises(Exception):
        ArtifactUploadRequest()  # type: ignore
