from datafetchers.codequalitydata_fetcher import CodeQualityDataFetcher


def test_fetch_codedata_aggregates_repo_tree(monkeypatch):
    fetcher = CodeQualityDataFetcher()
    fake_tree = [
        {"path": "tests/test_app.py"},
        {"path": ".github/workflows/ci.yml"},
        {"path": "setup.py"},
        {"path": "src/app.py"},
        {"path": "web/app.js"},
        {"path": "README.md"},
    ]
    monkeypatch.setattr(fetcher, "_fetch_repo_tree", lambda repo, branch="HEAD": fake_tree)

    result = fetcher.fetch_Codedata({"full_name": "org/repo", "default_branch": "main"})
    assert result["has_tests"] is True
    assert result["has_ci"] is True
    assert result["has_packaging"] is True
    assert result["has_readme"] is True
    # All code-like files (including tests and packaging) are counted
    assert result["total_code_files"] == 4
    assert result["language_counts"]["Python"] == 3
    assert result["language_counts"]["JavaScript"] == 1


def test_fetch_modeldata_falls_back_to_linked_repo(monkeypatch):
    fetcher = CodeQualityDataFetcher()
    # Sparse HF siblings so fallback triggers
    monkeypatch.setattr(fetcher, "_looks_sparse", lambda meta: True)
    monkeypatch.setattr(fetcher, "_fetch_hf_readme", lambda ident, kind="model": "github.com/org/proj")
    fake_tree = [{"path": "src/main.py"}, {"path": "tests/test_core.py"}]
    monkeypatch.setattr(fetcher, "_fetch_repo_tree", lambda repo, branch="HEAD": fake_tree)

    result = fetcher.fetch_Modeldata({"id": "m", "siblings": []})
    assert result["has_tests"] is True
    # Fallback repo tree contributes both source and test Python files
    assert result["language_counts"].get("Python") == 2
    assert result["total_code_files"] == 2
