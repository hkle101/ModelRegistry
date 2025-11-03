from pydantic import BaseModel, HttpUrl

class ModelUploadRequest(BaseModel):
    model_url: HttpUrl
