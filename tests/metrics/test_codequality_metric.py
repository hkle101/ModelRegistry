from metrics.codequality import CodeQualityMetric


def test_codequality_full_score():
    metric = CodeQualityMetric()
    data = {
        "has_tests": True,
        "has_ci": True,
        "has_lint_config": True,
        "language_counts": {"python": 30, "javascript": 10},
        "total_code_files": 100,
        "has_readme": True,
        "has_packaging": True,
    }

    result = metric.getScores(data)
    assert result["score"] == 1.0


def test_codequality_partial_score_with_diversity_bonus():
    metric = CodeQualityMetric()
    data = {
        "has_tests": False,
        "has_ci": False,
        "has_lint_config": False,
        "language_counts": {"python": 5, "javascript": 2, "go": 1},
        "total_code_files": 10,
        "has_readme": False,
        "has_packaging": True,
    }

    result = metric.getScores(data)
    # More generous weighting and scaling lift partial setups
    assert result["score"] == 0.26
