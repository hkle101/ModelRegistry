from datafetchers.performanceClaimsdata_fetcher import PerformanceClaimsDataFetcher


def test_performance_claims_data_fetcher_smoke():
    f = PerformanceClaimsDataFetcher()
    out = f.fetch_Modeldata({"model-index": [{"results": [1]}], "tags": ["benchmark"], "downloads": 10, "likes": 1})
    assert isinstance(out, dict)
