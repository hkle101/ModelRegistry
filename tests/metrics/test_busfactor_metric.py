import pytest
from metrics.busfactor import BusFactorMetric


def test_busfactor_scores_unique_authors_and_latency():
    metric = BusFactorMetric()
    result = metric.getScores({"commit_authors": ["a", "b", "a", "c", "d", "e"]})
    # 5 unique authors -> 0.5 with the more generous /10 scaling
    assert result["score"] == pytest.approx(0.5)
    assert result["latency"] >= 0


def test_busfactor_caps_and_handles_string_input():
    metric = BusFactorMetric()
    many_authors = [f"dev{i}" for i in range(60)]
    result = metric.getScores({"commit_authors": many_authors})
    assert result["score"] == 1.0

    metric.calculate_metric({"commit_authors": "solo"})
    # Single author still scores low but slightly higher than before
    assert metric.score == pytest.approx(0.1)
