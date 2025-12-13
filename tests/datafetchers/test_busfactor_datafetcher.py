import pytest
from datafetchers.busfactordata_fetcher import BusFactorDataFetcher


def test_fetch_codedata_dedupes_authors(monkeypatch):
    fetcher = BusFactorDataFetcher()
    monkeypatch.setattr(
        fetcher,
        "_fetch_commit_authors_from_github",
        lambda repo, per_page=100: ["a", "b", "a", "c"],
    )

    result = fetcher.fetch_Codedata({"full_name": "owner/repo"})
    assert result["commit_authors"] == ["a", "b", "c"]


def test_fetch_modeldata_reads_repo_from_readme(monkeypatch):
    fetcher = BusFactorDataFetcher()
    monkeypatch.setattr(fetcher, "_fetch_hf_readme", lambda ident, kind="model": "github.com/org/proj")
    monkeypatch.setattr(
        fetcher,
        "_fetch_commit_authors_from_github",
        lambda repo, per_page=100: ["dev1", "dev2"],
    )

    result = fetcher.fetch_Modeldata({"id": "some-model"})
    assert result["commit_authors"] == ["dev1", "dev2"]


def test_fetch_modeldata_returns_empty_when_no_repo(monkeypatch):
    fetcher = BusFactorDataFetcher()
    monkeypatch.setattr(fetcher, "_fetch_hf_readme", lambda ident, kind="model": None)
    result = fetcher.fetch_Modeldata({"id": "some-model"})
    assert result["commit_authors"] == []
