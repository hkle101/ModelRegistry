"""Data fetcher focused on dataset metadata.

This module exposes DatasetDataFetcher, which normalizes Hugging Face
dataset card information into the compact structure expected by
DatasetQualityMetric.
"""

from .basemetricdata_fetcher import BaseDataFetcher
from typing import Any, Dict

# import logging


class DatasetDataFetcher(BaseDataFetcher):
    """
    Data fetcher focused on dataset-specific metadata used by the
    DatasetQuality metric. It extracts a compact, normalized dict with
    fields the metric expects (dataset_url, code_url, description,
    cardData, siblings, tags, and a few engagement fields).
    """

    def __init__(self):
        super().__init__()

    def _extract_from_card(self, card: Any, key: str, default=None):
        if isinstance(card, dict):
            return card.get(key, default)
        return default

    def fetch_HFdata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract dataset-focused metadata from Hugging Face style dict.

        Returns a dict with keys the DatasetQuality metric will use.
        """
        self.metadata = {}
        if not isinstance(data, dict):
            return self.metadata

        card = data.get("cardData") or {}
        if not isinstance(card, dict):
            card = {}

        # Common fields and fallbacks
        dataset_url = (
            data.get("dataset")
            or data.get("url")
            or self._extract_from_card(card, "dataset_url", "")
        )
        code_url = data.get("code_url") or self._extract_from_card(card, "code_url", "")

        # description may live at top-level, in metadata, or in cardData
        description = (
            data.get("description")
            or data.get("metadata", {}).get("description")
            or self._extract_from_card(card, "description")
            or ""
        )

        siblings = (
            data.get("siblings") or data.get("metadata", {}).get("siblings") or []
        )
        tags = (
            data.get("tags")
            or data.get("metadata", {}).get("tags")
            or self._extract_from_card(card, "tags")
            or []
        )

        # Engagement-like fields
        downloads = (
            data.get("downloads")
            if data.get("downloads") is not None
            else self._extract_from_card(card, "downloads", 0)
        )
        likes = (
            data.get("likes")
            if data.get("likes") is not None
            else self._extract_from_card(card, "likes", 0)
        )

        # Normalize simple types
        try:
            downloads = int(downloads) if downloads is not None else 0
        except Exception:
            downloads = 0
        try:
            likes = int(likes) if likes is not None else 0
        except Exception:
            likes = 0

        # Store a compact metadata dict
        self.metadata.update(
            {
                "dataset_url": dataset_url or "",
                "code_url": code_url or "",
                "description": description,
                "cardData": card,
                "siblings": siblings,
                "tags": tags if isinstance(tags, list) else [],
                "downloads": downloads,
                "likes": likes,
            }
        )

        # logging.debug(f"DatasetDataFetcher collected keys={list(self.metadata.keys())}")
        return self.metadata

    # Implement BaseDataFetcher contract & provide aliases
    def fetch_Modeldata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.fetch_HFdata(data)

    def fetch_Datasetdata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.fetch_HFdata(data)

    def fetch_Codedata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # For code metadata, reuse HF extractor where possible
        return self.fetch_HFdata(data)
