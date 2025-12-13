from datafetchers.rampuptimedata_fetcher import RampUpTimeDataFetcher


def test_fetch_modeldata_normalizes_description_and_ids():
    fetcher = RampUpTimeDataFetcher()
    data = {
        "description": "Quick start instructions here",
        "cardData": {"description": "ignored"},
        "metadata": {"description": "also ignored"},
        "siblings": [{"rfilename": "README.md"}],
        "tags": ["tag1"],
        "widgetData": [1],
        "transformersInfo": {"auto_model": True},
        "id": "model-123",
    }
    result = fetcher.fetch_Modeldata(data)
    assert result["description"].startswith("Quick start")
    assert result["category"] == "MODEL"
    assert result["id"] == "model-123"
    assert result["siblings"][0]["rfilename"] == "README.md"


def test_fetch_codedata_sets_code_category():
    fetcher = RampUpTimeDataFetcher()
    data = {"description": "code repo", "full_name": "org/repo"}
    result = fetcher.fetch_Codedata(data)
    assert result["category"] == "CODE"
    assert result["description"] == "code repo"
    assert result["id"] == "org/repo"
