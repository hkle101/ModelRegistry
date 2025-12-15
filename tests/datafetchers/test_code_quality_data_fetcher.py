from datafetchers.codequalitydata_fetcher import CodeQualityDataFetcher


def test_code_quality_fetcher_from_repo_tree(monkeypatch):
    f = CodeQualityDataFetcher()
    monkeypatch.setattr(
        f,
        "_fetch_repo_tree",
        lambda repo, branch: [
            {"path": "README.md"},
            {"path": "tests/test_a.py"},
            {"path": ".github/workflows/ci.yml"},
            {"path": "pyproject.toml"},
        ],
    )

    out = f.fetch_Codedata({"full_name": "o/r", "default_branch": "main"})
    assert out["has_readme"] is True
    assert out["has_tests"] is True
    assert out["has_ci"] is True
    assert out["has_packaging"] is True
