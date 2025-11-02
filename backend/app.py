"""FastAPI application entrypoint for the model registry.

Run with: uvicorn backend.app:app --reload
"""

from fastapi import FastAPI

from backend.api import metrics as metrics_api
from backend.api import registry as registry_api

app = FastAPI(title="Model Registry API")


@app.get("/healthz")
def healthz():
    """Simple health check endpoint."""
    return {"status": "ok"}


app.include_router(metrics_api.router, prefix="/api/v1/metrics")
app.include_router(registry_api.router, prefix="/api/v1/models")

