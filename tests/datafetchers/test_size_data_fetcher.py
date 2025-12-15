from datafetchers.sizedata_fetcher import SizeDataFetcher


def test_size_data_fetcher_unknown_when_missing_fields():
    f = SizeDataFetcher()
    assert f.fetch_Modeldata({})["model_size_mb"] == "unknown"
