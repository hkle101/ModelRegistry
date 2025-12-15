from datafetchers.rampuptimedata_fetcher import RampUpTimeDataFetcher


def test_ramp_up_time_data_fetcher_sets_category_model_default():
    f = RampUpTimeDataFetcher()
    out = f.fetch_Modeldata({"description": "Quick start: do x", "id": "m"})
    assert out.get("category") == "MODEL"
