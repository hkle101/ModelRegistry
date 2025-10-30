from cli.utils.datafetchers.basemetricdata_fetcher import BaseDataFetcher
from typing import Any, Dict


class DatasetDataFetcher(BaseDataFetcher):
    """
    Fetch only the most relevant metadata for dataset quality scoring.
    """

    def __init__(self):
        super().__init__()

    def fetch_Modeldata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract dataset-relevant metadata fields.
        If a field is missing, fill it with 'unknown' or an empty fallback.
        """
        # Get license info using the shared fetcher

        return {
            "tags": data.get("cardData", {}).get("tags", []),
            "siblings": data.get("siblings", []),
            "author": data.get("author", "unknown"),
            "downloads": data.get("downloads", 0),
        }
