from .basemetricdata_fetcher import BaseDataFetcher
from typing import Any, Dict


class DatasetAndCodeDataFetcher(BaseDataFetcher):
    """
    Class for fetching dataset and code-related data.
    """

    def __init__(self):
        super().__init__()

    def fetch_Modeldata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return data.get("dataset", {"dataset": "unknown"})
