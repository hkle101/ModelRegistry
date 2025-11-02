from .basemetricdata_fetcher import BaseDataFetcher
from typing import Any, Dict


class SizeDataFetcher(BaseDataFetcher):
    """
    Class for fetching size-related data for models, converting to megabytes.
    """

    def __init__(self):
        super().__init__()

    def fetch_Modeldata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts model size information from Hugging Face metadata and converts to MB.

        Returns:
            dict: {'model_size_mb': float} or {'model_size_mb': 'unknown'} if not found
        """
        # Try to get safetensors total size
        safetensors = data.get("safetensors", {})
        total_size_bytes = safetensors.get("total")

        # If not found, fallback to usedStorage
        if total_size_bytes is None:
            total_size_bytes = data.get("usedStorage")

        if total_size_bytes is None:
            return {"model_size_mb": "unknown"}

        # Convert bytes to megabytes (1 MB = 1024*1024 bytes)
        total_size_mb = total_size_bytes / (1024 * 1024)

        return {"model_size_mb": round(total_size_mb, 2)}  # rounded to 2 decimals
