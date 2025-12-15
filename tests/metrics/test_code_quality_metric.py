from metrics.codequality import CodeQualityMetric


def test_code_quality_metric_smoke():
    m = CodeQualityMetric()
    m.calculate_metric(
        {
            "has_tests": True,
            "has_ci": True,
            "has_lint_config": True,
            "language_counts": {"Python": 10},
            "total_code_files": 20,
            "has_readme": True,
            "has_packaging": True,
        }
    )
    assert 0.0 <= float(m.score) <= 1.2
