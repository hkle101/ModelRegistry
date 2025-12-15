"""Dataset-and-code combined scoring metric implementation."""

from typing import Any, Dict
from .basemetric import BaseMetric


class DatasetAndCodeScoreMetric(BaseMetric):
    """
    Scores dataset and code signals using heuristics

    Input `data` is expected to be the structured dict produced by
    `datafetchers.datasetnCodedata_fetcher.DatasetAndCodeDataFetcher`.
    """

    def __init__(self):
        super().__init__()

    def calculate_metric(self, data: Dict[str, Any]):
        """Compute self.score from the provided structured data.

        The method is defensive: missing fields are treated as falsy/zero.
        """
        # Default
        score = 0.0

        if not data or not isinstance(data, dict):
            self.score = 0.0
            return

        # Documentation quality (slightly more generous thresholds/weights)
        if data.get("has_documentation"):
            desc = data.get("description") or ""
            desc_len = len(str(desc))
            if desc_len > 200:
                score += 0.35
            elif desc_len > 100:
                score += 0.25
            elif desc_len > 50:
                score += 0.15

        # Code examples – stronger signal for usability
        if data.get("has_code_examples"):
            score += 0.30

        # Dataset-specific example count
        category = (data.get("category") or "").upper()
        if category == "DATASET":
            try:
                example_count = int(data.get("example_count") or 0)
            except Exception:
                example_count = 0

            if example_count > 1_000_000:
                score += 0.25
            elif example_count > 100_000:
                score += 0.20
            elif example_count > 10_000:
                score += 0.15
            elif example_count > 1_000:
                score += 0.08
        elif category in {"MODEL", "CODE"}:
            if data.get("ml_integration"):
                score += 0.20

        # License weighting
        license_info = (data.get("licenses") or "").lower()
        if license_info and license_info not in {"unknown", "none", ""}:
            common_licenses = ["apache", "mit", "bsd", "gpl", "cc", "mozilla"]
            if any(lic in license_info for lic in common_licenses):
                score += 0.20
            else:
                score += 0.10

        # Engagement: downloads and likes
        engagement = data.get("engagement") or {}
        try:
            downloads = int(engagement.get("downloads", 0))
        except Exception:
            downloads = 0
        try:
            likes = int(engagement.get("likes", 0))
        except Exception:
            likes = 0

        # Engagement: more generous caps
        score += min(downloads / 1000.0, 0.15)
        score += min(likes / 100.0, 0.08)

        # Clamp to [0, 1] to ensure metric output stays in a normalized range
        score = max(0.0, min(score, 1.0))
        # Finalize
        self.score = round(score, 2)
        return
