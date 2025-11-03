from backend.app.models import ModelUploadRequest
from cli.utils.ModelManager import ModelManager

manager = ModelManager()

def upload_model(request: ModelUploadRequest):
    return manager.upload_model(request.model_url)

def get_model(name: str):
    return manager.get_model(name)

def list_models():
    return manager.list_models()

def delete_model(name: str):
    manager.delete_model(name)
    return True
