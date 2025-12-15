"""Data fetcher for ramp-up time signals.

This module exposes RampUpTimeDataFetcher, which normalizes model,
dataset, and code metadata into the fields expected by
RampUpTimeMetric (description, siblings, tags, widgets, etc.).
"""

from .basemetricdata_fetcher import BaseDataFetcher
from typing import Any, Dict


class RampUpTimeDataFetcher(BaseDataFetcher):
    """
    Class for fetching ramp-up time-related data.
    """

    def __init__(self):
        super().__init__()

    def fetch_Modeldata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Normalize common fields used by the RampUpTime metric implementation.
        # We prefer top-level description, but also include cardData and metadata blobs
        # so the metric can apply its heuristics.
        card = data.get("cardData") or {}
        metadata = data.get("metadata") or {}

        # Primary description candidates (noting that HF model cards are inconsistent)
        description = (
            data.get("description")
            or card.get("model_description")
            or card.get("description")
            or metadata.get("description")
            or ""
        )

        transformers_info = (
            data.get("transformersInfo") or metadata.get("transformersInfo") or {}
        )

        result: Dict[str, Any] = {
            "category": data.get("category", "MODEL"),
            "description": description,
            "cardData": card,
            "metadata": metadata,
            "siblings": data.get("siblings", []),
            "tags": data.get("tags", []) or metadata.get("tags", []),
            "widgetData": data.get("widgetData", []) or metadata.get("widgetData", []),
            "transformersInfo": transformers_info,
            # keep original id/name handy for downstream lookups
            "id": data.get("id") or data.get("modelId") or data.get("name") or "",
        }

        return result

    def fetch_Datasetdata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Datasets share the same card-style metadata on HF; ensure category is set.
        res = self.fetch_Modeldata(data)
        res["category"] = data.get("category", "DATASET")
        return res

    def fetch_Codedata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # For GitHub / code repos we expose similar fields but normalized from repo metadata.
        description = (
            data.get("description") or data.get("body") or data.get("readme") or ""
        )
        # siblings are not available for code repos; provide an empty list for uniformity.
        result: Dict[str, Any] = {
            "category": data.get("category", "CODE"),
            "description": description,
            "cardData": {},
            "metadata": {},
            "siblings": [],
            "tags": data.get("tags", []),
            "widgetData": [],
            "transformersInfo": {},
            "id": data.get("full_name") or data.get("name") or "",
        }

        return result
