import pytest
from cli.utils.MetricDataFetcher import MetricDataFetcher


def test_fetch_artifact_data_model(monkeypatch):
    fetcher = MetricDataFetcher()
    # Replace all fetchers with fakes that return distinct keys
    fake_fetchers = []
    for i in range(3):
        f = type("F", (), {})()
        f.fetch_Modeldata = lambda raw, i=i: {f"m{i}": i}
        f.fetch_Datasetdata = lambda raw, i=i: {f"d{i}": i}
        f.fetch_Codedata = lambda raw, i=i: {f"c{i}": i}
        fake_fetchers.append(f)
    fetcher.fetchers = fake_fetchers

    meta = {"artifact_type": "model", "download_url": "dl"}
    result = fetcher.fetch_artifact_data(meta)
    assert result == {"m0": 0, "m1": 1, "m2": 2, "download_url": "dl"}


def test_fetch_artifact_data_unknown_runs_all(monkeypatch):
    fetcher = MetricDataFetcher()
    f = type("F", (), {})()
    calls = {"m": 0, "d": 0, "c": 0}
    f.fetch_Modeldata = lambda raw: calls.__setitem__("m", calls["m"] + 1) or {"m": 1}
    f.fetch_Datasetdata = lambda raw: calls.__setitem__("d", calls["d"] + 1) or {"d": 1}
    f.fetch_Codedata = lambda raw: calls.__setitem__("c", calls["c"] + 1) or {"c": 1}
    fetcher.fetchers = [f]

    meta = {"artifact_type": "unknown", "download_url": None}
    result = fetcher.fetch_artifact_data(meta)
    assert result["m"] == 1 and result["d"] == 1 and result["c"] == 1
    assert calls == {"m": 1, "d": 1, "c": 1}
