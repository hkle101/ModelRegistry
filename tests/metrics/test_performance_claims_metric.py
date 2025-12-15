from metrics.performanceclaims import PerformanceClaimsMetric


def test_performance_claims_metric_smoke():
    m = PerformanceClaimsMetric()
    m.calculate_metric({"model_index": [{"results": [1, 2]}], "tags": ["benchmark"], "downloads": 1000, "likes": 10})
    assert m.score >= 0.0
