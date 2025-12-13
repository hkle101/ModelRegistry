from metrics.datasetandcodescore import DatasetAndCodeScoreMetric


def test_dataset_and_code_scores_dataset_signals():
    metric = DatasetAndCodeScoreMetric()
    data = {
        "has_documentation": True,
        "description": "A detailed dataset description" * 6,
        "has_code_examples": True,
        "category": "dataset",
        "example_count": 15000,
        "licenses": "apache-2.0",
        "engagement": {"downloads": 2000, "likes": 50},
    }

    result = metric.getScores(data)
    assert result["score"] == 0.85


def test_dataset_and_code_handles_missing_data():
    metric = DatasetAndCodeScoreMetric()
    result = metric.getScores({})
    assert result["score"] == 0.0
