from datafetchers.datasetdata_fetcher import DatasetDataFetcher


def test_fetch_hfdata_normalizes_fields():
    fetcher = DatasetDataFetcher()
    data = {
        "dataset": "https://example.com/ds",
        "description": "desc",
        "cardData": {"code_url": "https://example.com/code", "likes": "5"},
        "tags": ["a", "b"],
        "downloads": "10",
        "siblings": [{"rfilename": "README.md"}],
    }

    result = fetcher.fetch_HFdata(data)
    assert result["dataset_url"] == "https://example.com/ds"
    assert result["code_url"] == "https://example.com/code"
    assert result["downloads"] == 10
    assert result["likes"] == 5
    assert result["tags"] == ["a", "b"]
    assert result["siblings"][0]["rfilename"] == "README.md"


def test_fetch_hfdata_handles_missing_values():
    fetcher = DatasetDataFetcher()
    result = fetcher.fetch_HFdata({})
    assert result["dataset_url"] == ""
    assert result["code_url"] == ""
    assert result["downloads"] == 0
    assert result["likes"] == 0
