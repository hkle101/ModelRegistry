from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from backend.app.crud import upload_model, get_model, list_models, delete_model
import os

class ModelUploadRequest(BaseModel):
    model_url: str

app = FastAPI(title="ModelRegistry Backend")

# Serve the frontend from the 'frontend' folder
frontend_path = os.path.join(os.path.dirname(__file__), "../../frontend")
app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")

@app.get("/")
def serve_frontend():
    """Serve the frontend HTML page."""
    return FileResponse(os.path.join(frontend_path, "index.html"))

# -------------------- API Endpoints -------------------- #
@app.post("/upload")
def upload_endpoint(request: ModelUploadRequest):
    try:
        s3_path = upload_model(request.model_url)
        return {"s3_path": s3_path}
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
