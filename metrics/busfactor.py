"""Bus Factor scoring metric implementation."""

from typing import Any, Dict, Iterable
from .basemetric import BaseMetric


class BusFactorMetric(BaseMetric):
    """Scores Bus Factor using a list of commit authors.

    Contract:
      Input data keys:
        - commit_authors: Iterable[str] (optional). If missing or empty -> score 0.0
      Behavior:
        - Score is min(1.0, unique_author_count / 10.0)
          (10 unique contributors is treated as a strong bus factor).
        - Safe against non-list types and nulls; strings or other types won't crash
    """

    def __init__(self):
        super().__init__()

    def _normalize_authors(self, authors_val: Any) -> list[str]:
        if authors_val is None:
            return []
        if isinstance(authors_val, str):
            # single author as string
            a = authors_val.strip()
            return [a] if a else []
        # treat any iterable as list of strings, otherwise return empty
        if isinstance(authors_val, Iterable):
            out: list[str] = []
            for a in authors_val:
                try:
                    s = ("" if a is None else str(a)).strip()
                except Exception:
                    s = ""
                if s:
                    out.append(s)
            return out
        return []

    def calculate_metric(self, data: Dict[str, Any]):
        authors = self._normalize_authors(data.get("commit_authors"))
        unique_count = len(set(authors))
        if unique_count <= 0:
            self.score = 0.0
        else:
            # Normalize by 10 unique contributors (more generous), cap at 1.0
            self.score = min(1.0, unique_count / 10.0)