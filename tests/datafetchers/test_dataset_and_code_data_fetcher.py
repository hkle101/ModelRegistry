from datafetchers.datasetnCodedata_fetcher import DatasetAndCodeDataFetcher


def test_dataset_and_code_data_fetcher_smoke():
    f = DatasetAndCodeDataFetcher()
    out = f.fetch_Modeldata({"category": "DATASET", "cardData": {"dataset_info": {"splits": [{"num_examples": 10}]}}})
    assert isinstance(out, dict)
