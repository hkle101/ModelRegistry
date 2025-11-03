from backend.app.models import ModelUploadRequest
from aws.s3_helper import upload_model_metadata
from cli.utils.ModelManager import ModelManager

manager = ModelManager()

def upload_model(model_url: str) -> str:
    """Score the model and upload metadata to S3, returning the S3 path."""
    score_dict = manager.ScoreModel(model_url)
    s3_path = manager.SaveModelMetadata(score_dict)
    return s3_path

def get_model(name: str):
    return manager.GetModelMetadata(name)

def list_models():
    return manager.ListModels()

def delete_model(name: str):
    manager.DeleteModelMetadata(name)
    return True
