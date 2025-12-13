from metrics.rampuptime import RampUpTimeMetric


def test_rampuptime_scores_docs_and_examples():
    metric = RampUpTimeMetric()
    long_desc = "Quick start: pip install demo package. Usage tutorial example." * 10
    data = {
        "description": long_desc,
        "tags": ["bert", "transformers", "small"],
        "siblings": [
            {"rfilename": "README.md"},
            {"rfilename": "example.ipynb"},
            {"rfilename": "requirements.txt"},
        ],
        "widgetData": [{"example": 1}],
        "transformersInfo": {"auto_model": True},
        "category": "dataset",
    }

    result = metric.getScores(data)
    assert result["score"] == 1.0


def test_rampuptime_handles_missing_input():
    metric = RampUpTimeMetric()
    result = metric.getScores({})
    assert result["score"] == 0.0
