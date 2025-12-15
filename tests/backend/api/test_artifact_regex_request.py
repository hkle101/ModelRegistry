from backend.api.byregex import ArtifactRegExRequest


def test_artifact_regex_request_valid():
    m = ArtifactRegExRequest(regex="foo")
    assert m.regex == "foo"
