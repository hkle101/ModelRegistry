from metrics.sizescore import SizeScoreMetric


def test_size_score_metric_devices():
    m = SizeScoreMetric()
    out = m.getScores({"model_size_mb": 100})
    assert out["raspberry_pi"] == 1.0
    assert out["jetson_nano"] == 1.0
    assert out["desktop_pc"] == 1.0
    assert out["aws_server"] == 1.0
