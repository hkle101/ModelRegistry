from metrics.busfactor import BusFactorMetric


def test_bus_factor_metric_scales_unique_authors():
    m = BusFactorMetric()
    m.calculate_metric({"commit_authors": ["a", "b", "c", "d", "e"]})
    assert m.score == 0.5
