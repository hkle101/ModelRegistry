import json
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from cli.utils.MetricScorer import MetricScorer


def test_score_artifact_handles_metric_errors(monkeypatch):
    scorer = MetricScorer()
    # Force one metric to raise
    failing = MagicMock()
    failing.getScores.side_effect = Exception("boom")
    scorer.metrics["code_quality"] = failing

    data = {"any": "data"}
    result = scorer.score_artifact(data, as_json_str=False)

    assert result["code_quality"] == 0.0
    assert result["code_quality_latency"] == 0.0


def test_score_artifact_json_structure(monkeypatch):
    scorer = MetricScorer()

    # Provide deterministic metric outputs
    fixed = MagicMock()
    fixed.getScores.return_value = {"score": 0.8, "latency": 10}
    size = MagicMock()
    size.getScores.return_value = {
        "raspberry_pi": 0.7,
        "jetson_nano": 0.6,
        "desktop_pc": 0.9,
        "aws_server": 1.0,
        "latency": 20,
    }
    for key in scorer.metrics:
        scorer.metrics[key] = size if key == "size_score" else fixed

    data = {"any": "data"}
    raw = scorer.score_artifact(data, as_json_str=False)

    assert raw["size_score"]["desktop_pc"] == 0.9
    assert raw["code_quality"] == 0.8
    assert raw["net_score"] == pytest.approx(0.82, rel=1e-2)


def test_results_to_flat_rounding():
    scorer = MetricScorer()
    results = {
        "code_quality": Decimal("0.1234"),
        "code_quality_latency": Decimal("1.239"),
        "net_score": Decimal("0.4567"),
        "net_latency": Decimal("12.34"),
    }
    flat = scorer._results_to_flat(results)
    assert flat["code_quality"] == 0.12
    assert flat["code_quality_latency"] == 1.24
    assert flat["net_score"] == 0.46
    assert flat["net_latency"] == 12.34
