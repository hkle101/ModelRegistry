# backend/app/models.py
from pydantic import BaseModel
from typing import Optional

class ArtifactUploadRequest(BaseModel):
    url: str  # URL of HuggingFace model, dataset, or GitHub repo

class ArtifactMetadata(BaseModel):
    id: str
    type: str
    url: str
    name: Optional[str] = None

class ArtifactUpdateRequest(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None

class ArtifactQuery(BaseModel):
    type: Optional[str] = None
    name: Optional[str] = None

class ArtifactRegEx(BaseModel):
    regex: str
