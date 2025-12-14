from metrics.performanceclaims import PerformanceClaimsMetric


def test_performance_claims_reaches_cap_with_evidence():
    metric = PerformanceClaimsMetric()
    data = {
        "model_index": [{"results": [{"metric": "acc"}, {"metric": "f1"}]}],
        "tags": ["SOTA", "benchmark"],
        "downloads": 200000,
        "likes": 600,
    }

    result = metric.getScores(data)
    assert result["score"] == 1.0


def test_performance_claims_defaults_to_floor():
    metric = PerformanceClaimsMetric()
    result = metric.getScores({})
    assert result["score"] == 0.3
