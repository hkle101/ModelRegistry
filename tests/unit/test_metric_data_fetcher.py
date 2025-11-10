import pytest
from unittest.mock import MagicMock
from cli.utils.MetricDataFetcher import MetricDataFetcher  # adjust import if needed


@pytest.fixture
def mock_metric_fetcher():
    """Fixture returning a MetricDataFetcher with all sub-fetchers mocked."""
    fetcher = MetricDataFetcher()

    # Mock all fetchers so we control their outputs
    for f in fetcher.fetchers:
        f.fetch_Modeldata = MagicMock(return_value={"model_metric": 1})
        f.fetch_Datasetdata = MagicMock(return_value={"dataset_metric": 2})
        f.fetch_Codedata = MagicMock(return_value={"code_metric": 3})
    return fetcher


def test_fetch_model_data(mock_metric_fetcher):
    meta_info = {
        "artifact_type": "model",
        "raw_metadata": {"dummy": "data"}
    }

    result = mock_metric_fetcher.fetch_artifact_data(meta_info)

    # Only model data should appear
    assert result == {"model_metric": 1}

    for f in mock_metric_fetcher.fetchers:
        f.fetch_Modeldata.assert_called_once()
        f.fetch_Datasetdata.assert_not_called()
        f.fetch_Codedata.assert_not_called()


def test_fetch_dataset_data(mock_metric_fetcher):
    meta_info = {
        "artifact_type": "dataset",
        "raw_metadata": {"dummy": "data"}
    }

    result = mock_metric_fetcher.fetch_artifact_data(meta_info)

    assert result == {"dataset_metric": 2}

    for f in mock_metric_fetcher.fetchers:
        f.fetch_Datasetdata.assert_called_once()
        f.fetch_Modeldata.assert_not_called()
        f.fetch_Codedata.assert_not_called()


def test_fetch_code_data(mock_metric_fetcher):
    meta_info = {
        "artifact_type": "code",
        "raw_metadata": {"dummy": "data"}
    }

    result = mock_metric_fetcher.fetch_artifact_data(meta_info)

    assert result == {"code_metric": 3}

    for f in mock_metric_fetcher.fetchers:
        f.fetch_Codedata.assert_called_once()
        f.fetch_Modeldata.assert_not_called()
        f.fetch_Datasetdata.assert_not_called()


def test_fetch_unknown_type_calls_all(mock_metric_fetcher):
    meta_info = {
        "artifact_type": "unknown",
        "raw_metadata": {"dummy": "data"}
    }

    result = mock_metric_fetcher.fetch_artifact_data(meta_info)

    # Merged result (last write wins but values are unique keys so it's fine)
    assert result == {"model_metric": 1, "dataset_metric": 2, "code_metric": 3}

    for f in mock_metric_fetcher.fetchers:
        f.fetch_Modeldata.assert_called_once()
        f.fetch_Datasetdata.assert_called_once()
        f.fetch_Codedata.assert_called_once()


def test_fetch_handles_fetcher_exception(mock_metric_fetcher):
    # Break one fetcher: simulate a failure
    broken = mock_metric_fetcher.fetchers[0]
    broken.fetch_Modeldata.side_effect = Exception("boom")

    meta_info = {"artifact_type": "model", "raw_metadata": {}}
    result = mock_metric_fetcher.fetch_artifact_data(meta_info)

    # Should still return from other fetchers without crashing
    assert result == {"model_metric": 1}

    # Confirm broken fetcher still got called but didn't break the flow
    broken.fetch_Modeldata.assert_called_once()
