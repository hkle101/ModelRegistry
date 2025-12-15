from backend.api.list import ArtifactMetadata


def test_artifact_metadata_valid_minimal():
    m = ArtifactMetadata(name="n", id="a1", type="model")
    d = m.model_dump()
    assert d["name"] == "n"
    assert d["id"] == "a1"
    assert d["type"] == "model"
