import pytest

from datafetchers.busfactordata_fetcher import BusFactorDataFetcher


class _Resp:
    """Minimal requests-like response stub for `BusFactorDataFetcher` tests."""

    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


def test_bus_factor_data_fetcher_codedata(monkeypatch: pytest.MonkeyPatch):
    def fake_get(url, headers=None, timeout=10):
        assert "commits" in url
        return _Resp([
            {"author": {"login": "a"}},
            {"author": {"login": "b"}},
            {"author": {"login": "a"}},
        ])

    monkeypatch.setattr("datafetchers.busfactordata_fetcher.requests.get", fake_get)

    f = BusFactorDataFetcher()
    out = f.fetch_Codedata({"full_name": "o/r"})
    assert out["commit_authors"] == ["a", "b"]
