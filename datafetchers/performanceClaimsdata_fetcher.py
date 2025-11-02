from .basemetricdata_fetcher import BaseDataFetcher
from typing import Any, Dict


class PerformanceClaimsDataFetcher(BaseDataFetcher):
    """
    Class for fetching performance claims-related data.
    """

    def __init__(self):
        super().__init__()

    def fetch_Modeldata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return data.get("performance_claims", {"performance_claims": "unknown"})
