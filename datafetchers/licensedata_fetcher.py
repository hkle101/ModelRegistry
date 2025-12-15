"""Data fetcher for license metadata."""

from .basemetricdata_fetcher import BaseDataFetcher
from typing import Any, Dict


class LicenseDataFetcher(BaseDataFetcher):
    """
    Class for fetching license-related data.
    """

    def __init__(self):
        super().__init__()

    def fetch_HFdata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Initialize metadata dictionary
        self.metadata = {}
        # Fetch license
        license_name = None
        # Direct license field
        if "license" in data:
            license_name = data.get("license")
        # Check cardData section
        if not license_name and "cardData" in data:
            card_data = data.get("cardData", {})
            if isinstance(card_data, dict):
                license_name = card_data.get("license")
        # Check tags field
        if not license_name and "tags" in data:
            tags = data.get("tags", [])
            if isinstance(tags, list):
                for tag in tags:
                    if isinstance(tag, str) and tag.lower().startswith("license:"):
                        license_name = tag.split(":", 1)[1].strip()
                        break
        # Default fallback
        if not license_name:
            license_name = "unknown"
        # Normalize formatting
        license_name = str(license_name).strip().lower()
        # Store in metadata
        self.metadata["license"] = license_name
        # Return metadata dictionary
        return self.metadata

    def fetch_Datasetdata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.fetch_HFdata(data)

    def fetch_Modeldata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.fetch_HFdata(data)

    def fetch_Codedata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch the license for a GitHub repository from its API metadata.
        """
        # Initialize metadata dictionary
        self.metadata = {}
        license_info = data.get("license")
        license_name = "unknown"
        if isinstance(license_info, dict):
            # Prefer full name if available
            license_name = license_info.get("name") or "unknown"
        # Normalize formatting
        license_name = str(license_name).strip().lower()
        # Store in metadata
        self.metadata["license"] = license_name
        return self.metadata
