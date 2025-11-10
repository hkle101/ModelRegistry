import pytest
from unittest.mock import patch, MagicMock
from cli.utils.MetricScorer import MetricScorer  # adjust if your path is different


@pytest.fixture
def mock_metrics():
    """
    Mock all 8 metrics to return predictable scores and latencies.
    """
    # Regular metrics
    mock_score = MagicMock()
    mock_score.getScores.return_value = {"score": 0.8, "latency": 50.0}

    # Size score metric with device scores + latency key
    mock_size_score = MagicMock()
    mock_size_score.getScores.return_value = {
        "raspberry_pi": 0.7,
        "jetson_nano": 0.6,
        "desktop_pc": 0.9,
        "aws_server": 1.0,
        "size_score_latency": 100.0,  # key matches what MetricScorer expects
    }

    return {
        "code_quality": mock_score,
        "dataset_quality": mock_score,
        "dataset_and_code": mock_score,
        "bus_factor": mock_score,
        "license": mock_score,
        "size_score": mock_size_score,
        "ramp_up_time": mock_score,
        "performance_claims": mock_score,
    }


@patch("cli.utils.MetricScorer.CodeQualityMetric")
@patch("cli.utils.MetricScorer.DatasetQualityMetric")
@patch("cli.utils.MetricScorer.DatasetAndCodeScoreMetric")
@patch("cli.utils.MetricScorer.BusFactorMetric")
@patch("cli.utils.MetricScorer.LicenseMetric")
@patch("cli.utils.MetricScorer.SizeScoreMetric")
@patch("cli.utils.MetricScorer.RampUpTimeMetric")
@patch("cli.utils.MetricScorer.PerformanceClaimsMetric")
def test_score_artifact(
    mock_perf,
    mock_ramp,
    mock_size,
    mock_license,
    mock_bus,
    mock_dataset_code,
    mock_dataset_quality,
    mock_code_quality,
    mock_metrics,
):
    """
    Test that MetricScorer.score_artifact computes net_score and captures individual metric scores.
    """

    # Patch each metric class to return the corresponding mock
    mock_code_quality.return_value = mock_metrics["code_quality"]
    mock_dataset_quality.return_value = mock_metrics["dataset_quality"]
    mock_dataset_code.return_value = mock_metrics["dataset_and_code"]
    mock_bus.return_value = mock_metrics["bus_factor"]
    mock_license.return_value = mock_metrics["license"]
    mock_size.return_value = mock_metrics["size_score"]
    mock_ramp.return_value = mock_metrics["ramp_up_time"]
    mock_perf.return_value = mock_metrics["performance_claims"]

    scorer = MetricScorer()
    data = {"dummy": "data"}
    results = scorer.score_artifact(data)

    # Check that individual scores exist
    for name in [
        "code_quality",
        "dataset_quality",
        "dataset_and_code",
        "bus_factor",
        "license",
        "ramp_up_time",
        "performance_claims",
    ]:
        assert results[name] == 0.8
        assert results[f"{name}_latency"] == 50.0

    # Check size_score device scores
    assert results["raspberry_pi"] == 0.7
    assert results["jetson_nano"] == 0.6
    assert results["desktop_pc"] == 0.9
    assert results["aws_server"] == 1.0
    assert results["size_score_latency"] == 100.0

    # Check that net_score is calculated correctly (weighted sum)
    # Weighted net_score = sum(weights * scores)
    expected_net_score = (
        0.8 * 0.15 * 6  # 6 regular metrics
        + (0.7 + 0.6 + 0.9 + 1.0) / 4 * 0.1  # size_score average * weight
    )
    assert abs(results["net_score"] - round(expected_net_score, 2)) < 1e-5

    # Check that net_latency is a positive number
    assert results["net_latency"] > 0
