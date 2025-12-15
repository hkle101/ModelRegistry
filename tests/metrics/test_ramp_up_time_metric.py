import os

from metrics.rampuptime import RampUpTimeMetric


def test_ramp_up_time_metric_smoke_no_external_ai():
    os.environ.pop("GEN_AI_STUDIO_API_KEY", None)
    m = RampUpTimeMetric()
    m.calculate_metric({"description": "Quick start: install then run", "category": "MODEL"})
    assert m.score >= 0.0
