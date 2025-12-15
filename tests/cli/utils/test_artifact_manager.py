from cli.utils.ArtifactManager import ArtifactManager


def test_artifact_manager_process_url(monkeypatch):
    am = ArtifactManager()
    monkeypatch.setattr(am, "getArtifactData", lambda url: {"artifact_type": "model"})
    monkeypatch.setattr(am, "scoreArtifact", lambda data: {"net_score": 0.9})

    res = am.processUrl("https://github.com/org/repo")
    assert "artifact_id" in res
    assert res["name"] == "repo"
    assert res["scores"]["net_score"] == 0.9
