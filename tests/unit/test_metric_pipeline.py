from types import SimpleNamespace

from cli.utils.MetricDataFetcher import MetricDataFetcher
from cli.utils.MetricScorer import MetricScorer
from phase2.ModelRegistry.cli.utils.ArtifactManager import ModelManager


class StubFetcher:
    def __init__(self):
        self.called = []

    def fetch_Modeldata(self, data):
        self.called.append("model")
        return {"model_key": 1}

    def fetch_Datasetdata(self, data):
        self.called.append("dataset")
        return {"dataset_key": 2}

    def fetch_Codedata(self, data):
        self.called.append("code")
        return {"code_key": 3}


class StubMetric:
    def __init__(self, value=0.5, latency=12):
        self.value = value
        self.latency = latency

    def getScores(self, data):
        return {"score": self.value, "latency": self.latency}


def test_metric_data_fetcher_routes_by_artifact_type():
    mdf = MetricDataFetcher()
    # swap real fetchers with a single stub to make assertions easy
    stub = StubFetcher()
    mdf.fetchers = [stub]

    # model
    data = mdf.fetch_artifact_data(meta_info={
        "artifact_type": "model",
        "raw_metadata": {"any": 1},
    })
    assert data.get("model_key") == 1

    # dataset
    data = mdf.fetch_artifact_data(meta_info={
        "artifact_type": "dataset",
        "raw_metadata": {"any": 1},
    })
    assert data.get("dataset_key") == 2

    # code
    data = mdf.fetch_artifact_data(meta_info={
        "artifact_type": "code",
        "raw_metadata": {"any": 1},
    })
    assert data.get("code_key") == 3


def test_metric_scorer_aggregates_metrics_and_defaults():
    ms = MetricScorer()
    # override with two stub metrics and one that raises

    class Raising:
        def getScores(self, data):
            raise RuntimeError("boom")

    ms.metrics = {
        "m_ok": StubMetric(0.7, 10),
        "m_ok2": StubMetric(0.4, 20),
        "m_fail": Raising(),
    }

    result = ms.score_artifact({})
    assert result["m_ok"] == 0.7
    assert result["m_ok2"] == 0.4
    assert result["m_fail"] == 0.0  # default on error
    assert result["m_ok_latency"] == 10
    assert result["m_ok2_latency"] == 20
    assert result["m_fail_latency"] == 0.0


def test_model_manager_scoreartifact_structure(monkeypatch):
    mgr = ModelManager()

    # monkeypatch dependencies to avoid network/S3
    monkeypatch.setattr(
        mgr, "metadata_fetcher",
        SimpleNamespace(fetch=lambda url: {
            "artifact_type": "model",
            "raw_metadata": {"k": "v"},
        }),
    )
    monkeypatch.setattr(
        mgr, "metric_data_fetcher",
        SimpleNamespace(fetch_from_metadata=lambda meta: {"x": 1}),
    )
    monkeypatch.setattr(
        mgr, "scorer",
        SimpleNamespace(score_all_metrics=lambda data: {"scoreA": 1.0}),
    )

    out = mgr.ScoreArtifact("model", "https://example.com/m")
    assert out["type"] == "model"
    assert out["scores"]["scoreA"] == 1.0
    assert out["raw_metadata"] == {"k": "v"}
