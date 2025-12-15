from cli.utils.MetricScorer import MetricScorer


def test_metric_scorer_net_score_deterministic():
    class M:
        def __init__(self, score):
            self._score = score

        def getScores(self, data):
            return {"score": self._score, "latency": 1.0}

    class SizeM:
        def getScores(self, data):
            return {
                "raspberry_pi": 1.0,
                "jetson_nano": 1.0,
                "desktop_pc": 1.0,
                "aws_server": 1.0,
                "latency": 1.0,
            }

    scorer = MetricScorer()
    scorer.metrics = {
        "code_quality": M(1.0),
        "dataset_quality": M(0.0),
        "dataset_and_code": M(0.0),
        "bus_factor": M(0.0),
        "license": M(0.0),
        "size_score": SizeM(),
        "ramp_up_time": M(0.0),
        "performance_claims": M(0.0),
    }

    out = scorer.score_artifact({}, as_json_str=False)
    assert out["code_quality"] == 1.0
    assert out["size_score"]["raspberry_pi"] == 1.0
    assert out["net_score"] == float(scorer.weights["code_quality"] + scorer.weights["size_score"])
