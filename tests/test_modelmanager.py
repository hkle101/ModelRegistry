import pytest
from cli.utils.ModelManager import ModelManager

def test_model_lifecycle():
    manager = ModelManager()
    url = "https://huggingface.co/bert-base-uncased"

    score_dict = manager.ScoreModel(url)
    s3_path = manager.SaveModelMetadata(score_dict)
    assert score_dict["Name"] in manager.ListModels()

    metadata = manager.GetModelMetadata(score_dict["Name"])
    assert metadata["Name"] == score_dict["Name"]
    assert metadata["Scores"] == score_dict["Scores"]

    manager.DeleteModelMetadata(score_dict["Name"])
    assert score_dict["Name"] not in manager.ListModels()
