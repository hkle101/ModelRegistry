from datafetchers.datasetdata_fetcher import DatasetDataFetcher


def test_dataset_data_fetcher_extracts_description():
    f = DatasetDataFetcher()
    out = f.fetch_HFdata({"id": "d", "cardData": {"description": "x"}, "tags": ["t"]})
    assert "description" in out
