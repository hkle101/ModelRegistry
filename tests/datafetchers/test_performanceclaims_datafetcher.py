from datafetchers.performanceClaimsdata_fetcher import PerformanceClaimsDataFetcher


def test_fetch_hfdata_normalizes_and_defaults():
    fetcher = PerformanceClaimsDataFetcher()
    data = {
        "cardData": {"model-index": [{"results": [1]}], "likes": "7"},
        "tags": ["sota"],
        "downloads": "12",
        "category": "MODEL",
    }

    result = fetcher.fetch_HFdata(data)
    assert result["model_index"] == [{"results": [1]}]
    assert result["likes"] == 7
    assert result["downloads"] == 12
    assert result["category"] == "MODEL"
