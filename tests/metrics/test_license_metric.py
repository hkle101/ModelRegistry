import pytest
from metrics.license import LicenseMetric


@pytest.mark.parametrize(
    "license_name,expected",
    [
        ("apache-2.0", 1.0),
        ("mpl-2.0", 0.75),
        ("custom", 0.5),
        ("unknown", 0.0),
    ],
)
def test_license_metric_scoring(license_name, expected):
    metric = LicenseMetric()
    result = metric.getScores({"license": license_name})
    assert result["score"] == expected
