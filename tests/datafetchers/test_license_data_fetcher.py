from datafetchers.licensedata_fetcher import LicenseDataFetcher


def test_license_data_fetcher_from_tags():
    f = LicenseDataFetcher()
    out = f.fetch_Modeldata({"tags": ["license:MIT"]})
    assert out["license"] == "mit"
