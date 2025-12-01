import logging
from datetime import datetime
import json
import os
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware

from backend.deps import (
    artifact_manager as _artifact_manager,
    storage_manager as _storage_manager,
    verify_token as _verify_token,
)

from backend.api.health import router as health_router
from backend.api.create import router as create_router
from backend.api.list import router as list_router
from backend.api.retrieve import router as retrieve_router
from backend.api.reset import router as reset_router
from backend.api.license_check import router as license_router
from backend.api.lineage import router as lineage_router
from backend.api.rate import router as rate_router
from backend.api.update import router as update_router
from backend.api.cost import router as cost_router
from backend.api.byregex import router as byregex_router

# ============================================================
# Logging configuration
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")

# ============================================================
# File logger for request bodies
# ============================================================
log_file_path = os.path.join(os.path.dirname(__file__), "request_body.log")
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(file_handler)


# ============================================================
# JSON Body Logging Middleware
# ============================================================
class LogRequestBodyMiddleware(BaseHTTPMiddleware):
    """
    Logs endpoint and JSON request bodies to both console and file.
    """

    async def dispatch(self, request: Request, call_next):
        body = await request.body()
        log_entry = f"Incoming {request.method} {request.url.path}"

        if body:
            try:
                log_entry += f" Body: {body.decode()}"
            except Exception:
                log_entry += " (non-UTF8 body)"

        # Write log entry to both console and file
        logger.info(log_entry)

        # Re-attach the body so downstream endpoints can read it
        async def receive():
            return {"type": "http.request", "body": body}

        request._receive = receive

        return await call_next(request)


# ============================================================
# FastAPI application setup
# ============================================================
artifact_manager = _artifact_manager
storage_manager = _storage_manager
verify_token = _verify_token

app = FastAPI(title="Model Registry Backend")

# Add JSON logging middleware BEFORE everything else
app.add_middleware(LogRequestBodyMiddleware)

# ============================================================
# CORS configuration
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Timestamp injection middleware
# ============================================================
@app.middleware("http")
async def timestamp_middleware(request: Request, call_next):
    request_ts = datetime.utcnow().isoformat() + "Z"
    response = await call_next(request)
    response_ts = datetime.utcnow().isoformat() + "Z"

    response.headers["x-request-timestamp"] = request_ts
    response.headers["x-response-timestamp"] = response_ts

    try:
        if getattr(response, "media_type", None) == "application/json" and hasattr(
            response, "body"
        ):
            body = response.body.decode()
            data = json.loads(body)
            if isinstance(data, dict):
                data.setdefault(
                    "_timestamps", {"request": request_ts, "response": response_ts}
                )
                encoded = json.dumps(data).encode()
                response.body = encoded
                response.headers["content-length"] = str(len(encoded))
    except Exception:
        pass

    return response


# ============================================================
# Router registration
# ============================================================
app.include_router(health_router)
app.include_router(create_router)
app.include_router(list_router)
app.include_router(retrieve_router)
app.include_router(reset_router)
app.include_router(license_router)
app.include_router(lineage_router)
app.include_router(rate_router)
app.include_router(update_router)
app.include_router(cost_router)
app.include_router(byregex_router)

__all__ = ["app", "artifact_manager", "storage_manager", "verify_token"]
