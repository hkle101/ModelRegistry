"""Data fetcher for performance-claims metadata."""

from .basemetricdata_fetcher import BaseDataFetcher
from typing import Any, Dict


class PerformanceClaimsDataFetcher(BaseDataFetcher):
    """
    Data fetcher for performance-claims related fields.

    The PerformanceClaims metric expects a data dict containing at least
    the following keys (or reasonable fallbacks):
        - model_index: list or dict entries about model-index / results
        - tags: list of strings
        - cardData: dict with potential nested metadata
        - downloads: int
        - likes: int
        - category: string (e.g. 'MODEL')

    This class provides a robust `fetch_Modeldata` implementation used by
    the PerformanceClaims metric and mirrors patterns used in other
    datafetchers (license/size) in this repository.
    """

    def __init__(self):
        super().__init__()

    def _extract_from_card(self, card: Any, key: str, default=None):
        if isinstance(card, dict):
            return card.get(key, default)
        return default

    def fetch_HFdata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract performance-related metadata from Hugging Face model data."""
        self.metadata = {}

        # model-index may appear at top-level or inside cardData
        model_index = data.get("model-index")
        if model_index is None:
            card = data.get("cardData", {})
            model_index = self._extract_from_card(card, "model-index", [])

        tags = data.get("tags", [])
        if tags is None:
            tags = []

        card_data = data.get("cardData", {})
        if not isinstance(card_data, dict):
            card_data = {}

        # downloads/likes may exist at top-level or in cardData
        downloads = data.get("downloads")
        if downloads is None:
            downloads = self._extract_from_card(card_data, "downloads", 0)

        likes = data.get("likes")
        if likes is None:
            likes = self._extract_from_card(card_data, "likes", 0)

        # category sometimes provided as 'category' or 'type' in parsed sources
        category = data.get("category") or data.get("type") or "UNKNOWN"

        # Normalize simple types
        try:
            downloads = int(downloads) if downloads is not None else 0
        except Exception:
            downloads = 0
        try:
            likes = int(likes) if likes is not None else 0
        except Exception:
            likes = 0

        self.metadata.update(
            {
                "model_index": model_index if model_index is not None else [],
                "tags": tags if isinstance(tags, list) else [],
                "cardData": card_data,
                "downloads": downloads,
                "likes": likes,
                "category": category,
            }
        )

        return self.metadata

    # Keep BaseDataFetcher contract: implement fetch_Modeldata
    def fetch_Modeldata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Many callers supply the raw parsed metadata; use the HF extractor
        return self.fetch_HFdata(data)

    # Provide dataset alias so other parts of the code can reuse the logic
    def fetch_Datasetdata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.fetch_HFdata(data)
