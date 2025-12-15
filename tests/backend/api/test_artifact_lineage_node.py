from backend.api.lineage import ArtifactLineageNode


def test_artifact_lineage_node_valid():
    n = ArtifactLineageNode(artifact_id="a1", name="n", source="s")
    assert n.artifact_id == "a1"
