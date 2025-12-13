from metrics.sizescore import SizeScoreMetric


def test_sizescore_handles_known_size():
    metric = SizeScoreMetric()
    result = metric.getScores({"model_size_mb": 50})
    assert result["raspberry_pi"] == 1.0
    assert result["jetson_nano"] == 1.0
    assert result["desktop_pc"] == 1.0
    assert result["aws_server"] == 1.0
    assert result["latency"] >= 0


def test_sizescore_handles_unknown_size():
    metric = SizeScoreMetric()
    result = metric.getScores({"model_size_mb": "unknown"})
    assert result["raspberry_pi"] == 0.0
    assert result["jetson_nano"] == 0.0
    assert result["desktop_pc"] == 0.0
    assert result["aws_server"] == 0.0
