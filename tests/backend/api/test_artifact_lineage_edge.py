from backend.api.lineage import ArtifactLineageEdge


def test_artifact_lineage_edge_valid():
    e = ArtifactLineageEdge(from_node_artifact_id="a0", to_node_artifact_id="a1", relationship="base_model")
    assert e.relationship == "base_model"
