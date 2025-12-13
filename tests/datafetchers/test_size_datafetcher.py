from datafetchers.sizedata_fetcher import SizeDataFetcher


def test_size_fetcher_converts_bytes_to_mb():
    fetcher = SizeDataFetcher()
    data = {"safetensors": {"total": 1048576}}  # 1 MB in bytes
    result = fetcher.fetch_Modeldata(data)
    assert result["model_size_mb"] == 1.0


def test_size_fetcher_unknown_when_missing():
    fetcher = SizeDataFetcher()
    result = fetcher.fetch_Modeldata({})
    assert result["model_size_mb"] == "unknown"
