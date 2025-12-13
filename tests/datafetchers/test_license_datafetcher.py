from datafetchers.licensedata_fetcher import LicenseDataFetcher


def test_fetch_hfdata_reads_multiple_sources():
    fetcher = LicenseDataFetcher()
    data = {"cardData": {"license": "Apache-2.0"}, "tags": ["license:mit"]}
    result = fetcher.fetch_HFdata(data)
    assert result["license"] == "apache-2.0"


def test_fetch_codedata_prefers_license_name():
    fetcher = LicenseDataFetcher()
    data = {"license": {"name": "MIT License"}}
    result = fetcher.fetch_Codedata(data)
    assert result["license"] == "mit license"
