"""Registry API router: in-memory CRUD, ingest, reset endpoints.

This is a scaffold implementation suitable for tests and local runs. It uses
an in-memory store and simple ingestion rules (score >= 0.5 on non-latency
metrics) before accepting a model into the registry.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import threading
import json
import os

# Reuse MetricDataFetcher and MetricScorer from cli.utils to perform fetching
# and scoring. These modules are intentionally lightweight in the scaffold.
from cli.utils.MetricDataFetcher import MetricDataFetcher
from cli.utils.MetricScorer import MetricScorer
from backend.aws.s3_helper import estimate_model_size, upload_to_s3
from backend.database.connector import RDSConnector

router = APIRouter()

# In-memory store (thread-safe)
_store_lock = threading.Lock()
_models: Dict[int, Dict[str, Any]] = {}
_next_id = 1

# Users (simple in-memory admin). Passwords MUST NOT be stored here for real.
_users: Dict[str, Dict[str, Any]] = {}


def _load_default_admin():
    """Load default admin user from config if present, otherwise add placeholder."""
    cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "config", "default_users.json")
    # Try relative to repo root too
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    alt_path = os.path.join(repo_root, "config", "default_users.json")
    path = cfg_path if os.path.exists(cfg_path) else (alt_path if os.path.exists(alt_path) else None)
    if path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                admin = data.get("admin", {})
                username = admin.get("username", "admin")
                _users[username] = {"username": username, "role": "admin", "note": "default admin from config (password not stored)"}
                return
        except Exception:
            pass

    # Fallback placeholder
    _users["admin"] = {"username": "admin", "role": "admin", "note": "replace with secrets manager"}


_load_default_admin()


def _compute_non_latency_score(scores: Dict[str, Any]) -> float:
    """Compute mean of non-latency numeric scores. Handles nested dicts (e.g., size)."""
    vals: List[float] = []
    for k, v in scores.items():
        if k.endswith("_latency"):
            continue
        if k in ("name", "category"):
            continue
        if isinstance(v, (int, float)):
            vals.append(float(v))
        elif isinstance(v, dict):
            # include numeric values inside dicts
            for vv in v.values():
                if isinstance(vv, (int, float)):
                    vals.append(float(vv))
    if not vals:
        return 0.0
    return float(sum(vals) / len(vals))


@router.get("/health")
def health():
    """Registry health endpoint."""
    return {"status": "ok", "models_count": len(_models), "users": list(_users.keys())}


@router.post("/reset")
def reset_registry():
    """Reset in-memory registry to default state (empty models, default admin)."""
    global _models, _next_id, _users
    with _store_lock:
        _models = {}
        _next_id = 1
        _users = {}
        _load_default_admin()
    return {"status": "reset", "models_count": 0, "users": list(_users.keys())}


@router.get("/")
def list_models(page: int = 1, size: int = 10):
    """Paginated list of models."""
    if page < 1 or size < 1:
        raise HTTPException(status_code=400, detail="page and size must be >= 1")
    with _store_lock:
        items = list(_models.values())
    start = (page - 1) * size
    end = start + size
    return {"total": len(items), "page": page, "size": size, "items": items[start:end]}


@router.post("/ingest")
def ingest_model(url: Dict[str, str]):
    """Ingest a public model by URL. Only accept if non-latency mean score >= 0.5.

    Request body: {"url": "https://huggingface.co/..."}
    """
    if not isinstance(url, dict) or "url" not in url:
        raise HTTPException(status_code=400, detail="Provide a JSON body with 'url' field")
    model_url = url["url"]

    # Fetch model metadata and compute metric scores using MetricDataFetcher/MetricScorer
    fetcher = MetricDataFetcher()
    scorer = MetricScorer()
    try:
        model_data = fetcher.fetch_Modeldata(model_url)
        scores = scorer.score_all_metrics(model_data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"error fetching/scoring model: {e}")

    mean_score = _compute_non_latency_score(scores)
    if mean_score < 0.5:
        raise HTTPException(status_code=400, detail=f"model score {mean_score:.3f} below ingest threshold")

    # enrich metadata with estimated size (MB) if available
    size_mb = estimate_model_size(model_data)
    if size_mb is not None:
        model_data["model_size_mb"] = size_mb

    # persist into in-memory store and call RDS stub
    global _next_id
    with _store_lock:
        model_id = _next_id
        _next_id += 1
        entry = {
            "id": model_id,
            "url": model_url,
            "metadata": model_data,
            "scores": scores,
            "ingest_score": mean_score,
        }
        _models[model_id] = entry

    # persist to RDS stub (file-backed)
    try:
        rds = RDSConnector()
        rds.save_model(entry)
    except Exception:
        # non-fatal for scaffold; keep in-memory copy
        pass

    return {"status": "ingested", "id": model_id, "ingest_score": mean_score}


@router.post("/")
def create_model(payload: Dict[str, Any]):
    """Create a model record manually (metadata provided in payload)."""
    global _next_id
    with _store_lock:
        model_id = _next_id
        _next_id += 1
        entry = {"id": model_id, **payload}
        _models[model_id] = entry
    return entry


@router.get("/{model_id}")
def get_model(model_id: int):
    with _store_lock:
        m = _models.get(model_id)
    if not m:
        raise HTTPException(status_code=404, detail="model not found")
    return m


@router.put("/{model_id}")
def update_model(model_id: int, payload: Dict[str, Any]):
    with _store_lock:
        if model_id not in _models:
            raise HTTPException(status_code=404, detail="model not found")
        _models[model_id].update(payload)
        return _models[model_id]


@router.delete("/{model_id}")
def delete_model(model_id: int):
    with _store_lock:
        if model_id in _models:
            del _models[model_id]
            return {"status": "deleted", "id": model_id}
    raise HTTPException(status_code=404, detail="model not found")
