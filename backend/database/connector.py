"""RDS connector stub for persisting registry entries.

This is a simple file-backed stub used for local testing. Replace with a
real database client (psycopg2, SQLAlchemy, or SQLModel) in production.
"""

from typing import Dict, Any, List, Optional
import json
import threading
import os

_lock = threading.Lock()


class RDSConnector:
    """Simple JSON-file backed connector used as a scaffold.

    Data is stored in `backend/database/store.json` as a list of model entries.
    """

    def __init__(self, path: Optional[str] = None):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        default = os.path.join(repo_root, "backend", "database", "store.json")
        self.path = path or default
        # ensure file exists
        if not os.path.exists(os.path.dirname(self.path)):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _read_all(self) -> List[Dict[str, Any]]:
        with _lock:
            with open(self.path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except Exception:
                    return []

    def _write_all(self, data: List[Dict[str, Any]]) -> None:
        with _lock:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def save_model(self, entry: Dict[str, Any]) -> None:
        data = self._read_all()
        data.append(entry)
        self._write_all(data)

    def delete_model(self, model_id: int) -> bool:
        data = self._read_all()
        new = [d for d in data if d.get("id") != model_id]
        if len(new) == len(data):
            return False
        self._write_all(new)
        return True

    def list_models(self) -> List[Dict[str, Any]]:
        return self._read_all()

    def get_model(self, model_id: int) -> Optional[Dict[str, Any]]:
        for d in self._read_all():
            if d.get("id") == model_id:
                return d
        return None
