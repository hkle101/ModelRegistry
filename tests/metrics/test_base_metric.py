from metrics.basemetric import BaseMetric


def test_base_metric_getscores_records_latency():
    class M(BaseMetric):
        def calculate_metric(self, data):
            self.score = 0.33

    m = M()
    out = m.getScores({})
    assert out["score"] == 0.33
    assert out["latency"] >= 0.0
