from unittest.mock import patch
from phase2.ModelRegistry.cli.utils.ArtifactManager import ModelManager


def test_list_artifacts_filters_by_type():
    mgr = ModelManager()
    fake_items = [
        {"model_name": "m1", "artifact_type": "model"},
        {"model_name": "d1", "artifact_type": "dataset"},
    ]
    with patch(
        "cli.utils.ModelManager.list_metadata_from_s3", return_value=fake_items
    ):
        models = mgr.ListArtifacts(artifact_type="model")
        assert len(models) == 1
        assert models[0]["id"] == "m1"


def test_get_and_delete_wire_through():
    mgr = ModelManager()
    with patch(
        "cli.utils.ModelManager.get_metadata_from_s3",
        return_value={"ok": True},
    ) as g:
        with patch(
            "cli.utils.ModelManager.delete_metadata_from_s3", return_value=None
        ) as d:
            meta = mgr.GetArtifactMetadata("model", "m1")
            assert meta == {"ok": True}
            mgr.DeleteArtifactMetadata("model", "m1")
            # Ensure underlying helpers were called with type & id
            g.assert_called_once_with("m1", "model")
            d.assert_called_once_with("m1", "model")
