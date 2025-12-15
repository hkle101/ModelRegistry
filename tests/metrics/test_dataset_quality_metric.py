import os

from metrics.datasetquality import DatasetQualityMetric


def test_dataset_quality_metric_heuristic_path():
    os.environ.pop("GEN_AI_STUDIO_API_KEY", None)
    m = DatasetQualityMetric()
    m.calculate_metric({"description": "This dataset includes examples and usage.", "category": "DATASET"})
    assert m.score >= 0.0
