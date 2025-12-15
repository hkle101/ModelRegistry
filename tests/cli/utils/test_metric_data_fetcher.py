from cli.utils.MetricDataFetcher import MetricDataFetcher


def test_metric_data_fetcher_calls_correct_fetcher_method():
    calls = []

    class F:
        def fetch_Modeldata(self, data):
            calls.append("m")
            return {"m": 1}

        def fetch_Datasetdata(self, data):
            calls.append("d")
            return {"d": 1}

        def fetch_Codedata(self, data):
            calls.append("c")
            return {"c": 1}

    mdf = MetricDataFetcher()
    mdf.fetchers = [F()]

    out = mdf.fetch_artifact_data({"artifact_type": "model", "download_url": "u"})
    assert out["m"] == 1
    assert out["download_url"] == "u"
    assert calls == ["m"]
