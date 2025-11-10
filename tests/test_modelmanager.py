import pytest
from phase2.ModelRegistry.cli.utils.ArtifactManager import ModelManager


@pytest.mark.integration
def test_model_lifecycle():
    manager = ModelManager()
    url = "https://huggingface.co/bert-base-uncased"

    # Score and save a model artifact
    score_dict = manager.ScoreArtifact("model", url)
    manager.SaveArtifactMetadata("model", score_dict)
    assert score_dict["id"] in manager.ListArtifacts("model")

    metadata = manager.GetArtifactMetadata("model", score_dict["id"])
    assert metadata["Name"] == score_dict["id"]
    assert metadata["Scores"] == score_dict["scores"]

    manager.DeleteArtifactMetadata("model", score_dict["id"])
    assert score_dict["id"] not in manager.ListArtifacts("model")
