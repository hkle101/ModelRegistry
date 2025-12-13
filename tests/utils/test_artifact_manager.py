from cli.utils.ArtifactManager import ArtifactManager


def test_extract_name_from_url():
    mgr = ArtifactManager()
    assert mgr._extract_name_from_url("https://github.com/user/repo.git") == "repo"
    assert mgr._extract_name_from_url("https://example.com/") == "unknown_artifact"


def test_process_url_happy_path(monkeypatch):
    mgr = ArtifactManager()
    fake_data = {"foo": "bar"}
    fake_scores = {"score": 1}

    monkeypatch.setattr(mgr.metadatafetcher, "fetch", lambda url: {"artifact_type": "model"})
    monkeypatch.setattr(mgr.metricdatafetcher, "fetch_artifact_data", lambda meta: fake_data)
    monkeypatch.setattr(mgr.scorer, "score_artifact", lambda data: fake_scores)

    result = mgr.processUrl("https://github.com/user/repo")
    assert result["foo"] == "bar"
    assert result["scores"] == fake_scores
    assert result["name"] == "repo"
    assert "artifact_id" in result
