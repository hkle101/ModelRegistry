from fastapi import FastAPI, HTTPException
from app.models import ModelUploadRequest
from app.crud import upload_model, get_model, list_models, delete_model

app = FastAPI(title="ModelRegistry Backend")

@app.post("/upload")
def upload_endpoint(request: ModelUploadRequest):
    try:
        return {"s3_path": upload_model(request.model_url)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
def list_endpoint():
    return list_models()

@app.get("/models/{name}")
def get_endpoint(name: str):
    try:
        return get_model(name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/models/{name}")
def delete_endpoint(name: str):
    try:
        delete_model(name)
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
