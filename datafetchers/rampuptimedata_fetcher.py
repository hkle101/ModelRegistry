from .basemetricdata_fetcher import BaseDataFetcher
from typing import Any, Dict


class RampUpTimeDataFetcher(BaseDataFetcher):
    """
    Class for fetching ramp-up time-related data.
    """

    def __init__(self):
        super().__init__()

    def fetch_Modeldata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return data.get("ramp_up_time", {"ramp_up_time": "unknown"})
