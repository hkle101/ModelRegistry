from backend.api.list import ArtifactQuery


def test_artifact_query_valid_name_only():
    q = ArtifactQuery(name="*")
    assert q.name == "*"
    assert q.types is None


def test_artifact_query_valid_types():
    q = ArtifactQuery(name="foo", types=["model", "code"])
    assert q.types == ["model", "code"]
