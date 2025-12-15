import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pytest


@dataclass
class DummyResponse:
    """Minimal requests-like response for unit tests."""

    status_code: int = 200
    _json: Any = None
    content: bytes = b""

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeArtifactManager:
    """In-memory ArtifactManager used by API e2e tests."""

    def __init__(self):
        self._n = 0

    def processUrl(self, url: str) -> Dict[str, Any]:
        self._n += 1
        artifact_id = f"t{self._n}"
        name = url.rstrip("/").split("/")[-1] or "artifact"
        return {
            "artifact_id": artifact_id,
            "name": name,
            "artifact_type": "model",
            "processed_url": url,
            "download_url": f"https://example.com/{artifact_id}.bin",
            "scores": {"net_score": 0.5, "name": "", "category": ""},
        }

    def getArtifactData(self, url: str) -> Dict[str, Any]:
        return {"processed_url": url, "artifact_type": "model"}

    def scoreArtifact(self, artifact_data: Dict[str, Any]):
        return {"net_score": 0.42, "name": "", "category": ""}


class FakeStorageManager:
    """In-memory StorageManager used by API e2e tests."""

    def __init__(self, artifact_manager: Optional[FakeArtifactManager] = None):
        self.items: Dict[str, Dict[str, Any]] = {}
        self.artifact_manager = artifact_manager or FakeArtifactManager()
        self.bucket_name = "fake-bucket"

    def store_artifact(self, artifact_data: Dict[str, Any], artifact_bytes: bytes, filename: str) -> bool:
        artifact_id = artifact_data["artifact_id"]
        name = artifact_data.get("name") or filename or artifact_id
        artifact_type = artifact_data.get("artifact_type") or artifact_data.get("type") or "model"
        self.items[artifact_id] = {
            "artifact_id": artifact_id,
            "name": name,
            "type": artifact_type,
            "artifact_type": artifact_type,
            "processed_url": artifact_data.get("processed_url", ""),
            "download_url": artifact_data.get("download_url", ""),
            "url": f"s3://{self.bucket_name}/artifacts/{artifact_id}/{name}",
            "scores": artifact_data.get("scores"),
            "metadata": artifact_data.get("metadata", {}),
            "size_in_gb": artifact_data.get("size_in_gb", 1.0),
        }
        return True

    def get_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        return self.items.get(artifact_id)

    def delete_artifact(self, artifact_id: str) -> bool:
        return self.items.pop(artifact_id, None) is not None

    def reset(self) -> bool:
        self.items.clear()
        return True

    def generate_download_url(self, artifact_id: str, filename: str, expires_in: int = 3600) -> str:
        return f"https://example.com/download/{artifact_id}/{filename}?expires={expires_in}"

    def list_artifacts(self, queries: List[Dict[str, Any]], offset: Optional[int] = 0, page_size: int = 10) -> Dict[str, Any]:
        all_items = list(self.items.values())

        norm_queries: List[Dict[str, Any]] = []
        for q in queries:
            name = q.get("name", "*")
            types = q.get("types") or []
            norm_queries.append({"name": name, "types": [str(t).lower() for t in types]})

        def match(item: Dict[str, Any], q: Dict[str, Any]) -> bool:
            name_filter = q["name"]
            name_ok = True if name_filter == "*" else name_filter.lower() in str(item.get("name", "")).lower()
            types_needed = q["types"]
            stored_type = str(item.get("type") or item.get("artifact_type") or "").lower()
            type_ok = True if not types_needed else stored_type in types_needed
            return name_ok and type_ok

        filtered = [it for it in all_items if any(match(it, nq) for nq in norm_queries)]
        start = int(offset or 0)
        end = min(start + int(page_size), len(filtered))
        page = filtered[start:end]
        next_offset = end if end < len(filtered) else None

        items = [
            {
                "name": it.get("name"),
                "id": it.get("artifact_id"),
                "type": it.get("type") or it.get("artifact_type"),
                "url": it.get("url"),
                "download_url": it.get("download_url"),
            }
            for it in page
        ]
        return {"items": items, "next_offset": next_offset}

    def search_artifacts_by_regex(self, regex: str) -> List[Dict[str, Any]]:
        pattern = re.compile(regex, re.IGNORECASE)
        out = []
        for it in self.items.values():
            name = it.get("name", "")
            readme = (it.get("metadata") or {}).get("readme", "")
            if pattern.search(str(name)) or pattern.search(str(readme)):
                out.append(it)
        return out


@pytest.fixture()
def fake_artifact_manager() -> FakeArtifactManager:
    return FakeArtifactManager()


@pytest.fixture()
def fake_storage_manager(fake_artifact_manager: FakeArtifactManager) -> FakeStorageManager:
    return FakeStorageManager(artifact_manager=fake_artifact_manager)


@pytest.fixture()
def patch_backend_deps(monkeypatch: pytest.MonkeyPatch, fake_storage_manager: FakeStorageManager, fake_artifact_manager: FakeArtifactManager):
    """Patch backend modules to use fake managers (avoids AWS/network)."""
    import backend.deps as deps

    monkeypatch.setattr(deps, "storage_manager", fake_storage_manager, raising=True)
    monkeypatch.setattr(deps, "artifact_manager", fake_artifact_manager, raising=True)

    # Routers import manager singletons directly, so patch their module globals too.
    import backend.api.create as create
    import backend.api.list as list_api
    import backend.api.retrieve as retrieve
    import backend.api.delete as delete
    import backend.api.download as download
    import backend.api.byregex as byregex
    import backend.api.rate as rate
    import backend.api.cost as cost
    import backend.api.reset as reset
    import backend.api.license_check as license_check
    import backend.api.lineage as lineage

    for mod in [create, list_api, retrieve, delete, download, byregex, rate, cost, reset, license_check, lineage]:
        if hasattr(mod, "storage_manager"):
            monkeypatch.setattr(mod, "storage_manager", fake_storage_manager, raising=True)
        if hasattr(mod, "artifact_manager"):
            monkeypatch.setattr(mod, "artifact_manager", fake_artifact_manager, raising=True)

    return True
