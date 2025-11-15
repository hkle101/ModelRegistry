import pytest
from unittest.mock import MagicMock
from cli.utils.ArtifactManager import ArtifactManager


@pytest.fixture
def mock_dependencies():
    """Fixture providing mock dependencies for ArtifactManager."""
    return {
        "metadatafetcher": MagicMock(),
        "metricdatafetcher": MagicMock(),
        "scorer": MagicMock(),
    }


@pytest.fixture
def artifact_manager(mock_dependencies):
    """Fixture initializing ArtifactManager with mocked dependencies."""
    manager = ArtifactManager()
    manager.metadatafetcher = mock_dependencies["metadatafetcher"]
    manager.metricdatafetcher = mock_dependencies["metricdatafetcher"]
    manager.scorer = mock_dependencies["scorer"]
    return manager


class TestArtifactManager:
    """Unit tests for ArtifactManager."""

    def test_extract_name_from_url(self, artifact_manager):
        url = "https://github.com/user/repo.git"
        result = artifact_manager._extract_name_from_url(url)
        assert result == "repo"

    def test_get_artifact_data(self, artifact_manager):
        mock_meta = {"repo": "data"}
        mock_artifact = {"artifact": "info"}

        artifact_manager.metadatafetcher.fetch.return_value = mock_meta
        artifact_manager.metricdatafetcher.fetch_artifact_data.return_value = mock_artifact

        result = artifact_manager.getArtifactData("https://github.com/user/repo")

        artifact_manager.metadatafetcher.fetch.assert_called_once_with("https://github.com/user/repo")
        artifact_manager.metricdatafetcher.fetch_artifact_data.assert_called_once_with(mock_meta)
        assert result == mock_artifact

    def test_score_artifact(self, artifact_manager):
        mock_scores = {"score": 100}
        artifact_data = {"some": "data"}

        artifact_manager.scorer.score_artifact.return_value = mock_scores
        result = artifact_manager.scoreArtifact(artifact_data)

        artifact_manager.scorer.score_artifact.assert_called_once_with(artifact_data)
        assert result == mock_scores

    def test_process_url(self, artifact_manager):
        url = "https://github.com/user/repo"
        mock_artifact_data = {"data": "value"}
        mock_scores = {"score": 10}

        artifact_manager.metadatafetcher.fetch.return_value = {"meta": "info"}
        artifact_manager.metricdatafetcher.fetch_artifact_data.return_value = mock_artifact_data
        artifact_manager.scorer.score_artifact.return_value = mock_scores

        result = artifact_manager.processUrl(url)

        assert "artifact_id" in result
        assert "name" in result and result["name"] == "repo"
        assert result["scores"] == mock_scores
        assert result["data"] == "value"


