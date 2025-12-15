from backend.api.lineage import ArtifactLineageGraph, ArtifactLineageNode, ArtifactLineageEdge


def test_artifact_lineage_graph_valid():
    g = ArtifactLineageGraph(
        nodes=[ArtifactLineageNode(artifact_id="a1", name="n", source="s")],
        edges=[ArtifactLineageEdge(from_node_artifact_id="a0", to_node_artifact_id="a1", relationship="r")],
    )
    assert len(g.nodes) == 1
    assert len(g.edges) == 1
