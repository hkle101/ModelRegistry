from datafetchers.datasetnCodedata_fetcher import DatasetAndCodeDataFetcher


def test_fetch_hfdata_dataset_fields_and_examples():
    fetcher = DatasetAndCodeDataFetcher()
    data = {
        "category": "DATASET",
        "description": "Comprehensive description for dataset with ample details" * 2,
        "cardData": {
            "dataset_info": {
                "splits": [
                    {"name": "train", "num_examples": 1000},
                    {"name": "test", "num_examples": 500},
                ]
            },
            "license": "apache-2.0",
        },
        "tags": ["license:mit", "transformers"],
        "siblings": [{"rfilename": "README.md"}, {"rfilename": "example.ipynb"}],
        "widgetData": [{"example": 1}],
        "downloads": 200,
        "likes": 10,
    }

    result = fetcher.fetch_HFdata(data)
    assert result["category"] == "DATASET"
    assert result["example_count"] == 1500
    assert result["licenses"].lower().startswith("apache")
    assert result["has_documentation"] is True
    assert result["has_code_examples"] is True
    assert result["ml_integration"] is True
    assert result["engagement"]["downloads"] == 200
    assert result["engagement"]["likes"] == 10


def test_fetch_hfdata_sets_sane_defaults_for_empty():
    fetcher = DatasetAndCodeDataFetcher()
    result = fetcher.fetch_HFdata({})
    assert result["category"] == "UNKNOWN"
    assert result["example_count"] == 0
    assert result["licenses"] == ""
    assert result["has_documentation"] is False
    assert result["has_code_examples"] is False
