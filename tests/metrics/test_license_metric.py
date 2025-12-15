from metrics.license import LicenseMetric


def test_license_metric_mit_is_high_quality():
    m = LicenseMetric()
    m.calculate_metric({"license": "mit"})
    assert m.score == 1.0
