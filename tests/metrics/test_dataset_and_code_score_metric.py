from metrics.datasetandcodescore import DatasetAndCodeScoreMetric


def test_dataset_and_code_score_metric_rewards_docs_and_examples():
    m = DatasetAndCodeScoreMetric()
    m.calculate_metric({"has_documentation": True, "description": "x" * 250, "has_code_examples": True})
    assert m.score > 0.0
