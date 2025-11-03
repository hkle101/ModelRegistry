import pytest
from aws.s3_helper import (
    upload_model_metadata,
    get_model_metadata,
    list_models,
    delete_model_metadata,
)

@pytest.mark.integration
def test_s3_crud_cycle():
    """Test full S3 CRUD cycle for model metadata."""
    model_name = "test_model_crud"
    url = "https://huggingface.co/bert-base-uncased"
    scores = {"accuracy": 0.95, "loss": 0.1}

    # 1️⃣ Upload metadata
    s3_path = upload_model_metadata(model_name, scores, url)
    assert s3_path.startswith("s3://"), "Upload should return valid S3 path"

    # 2️⃣ List models should include our uploaded one
    models = list_models()
    assert model_name in models, f"{model_name} not found in S3 list"

    # 3️⃣ Retrieve metadata and verify correctness
    metadata = get_model_metadata(model_name)
    assert metadata["Name"] == model_name
    assert metadata["Scores"] == scores
    assert metadata["url"] == url

    # 4️⃣ Delete model metadata
    delete_model_metadata(model_name)
    models_after_delete = list_models()
    assert model_name not in models_after_delete, "Model was not deleted from S3"
