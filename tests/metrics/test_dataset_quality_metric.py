import pytest
from metrics.datasetquality import DatasetQualityMetric


@pytest.fixture
def metric_no_llm(monkeypatch):
    metric = DatasetQualityMetric()
    monkeypatch.setattr(metric.datafetcher, "fetch_HFdata", lambda data: data)
    monkeypatch.delenv("GEN_AI_STUDIO_API_KEY", raising=False)
    return metric


def test_dataset_quality_heuristic_hits_cap(metric_no_llm):
    data = {
        "dataset_url": "https://example.com/dataset",
        "code_url": "https://example.com/code",
        "description": "Comprehensive dataset with examples " * 5,
        "siblings": [
            {"rfilename": "README.md"},
            {"rfilename": "example_notebook.ipynb"},
        ],
        "tags": ["transformers", "nlp"],
        "cardData": {"transformersInfo": {"auto_model": True}, "widgetData": [{"ex": 1}]},
        "downloads": 5000,
        "likes": 200,
    }

    result = metric_no_llm.getScores(data)
    assert result["score"] == 1.0


def test_dataset_quality_handles_empty_input(metric_no_llm):
    result = metric_no_llm.getScores({})
    assert result["score"] == 0.0
