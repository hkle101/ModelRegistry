from typing import Any, Dict
from .basemetric import BaseMetric


class PerformanceClaimsMetric(BaseMetric):
    """
    Class for scoring Performance Claims Metric
    """

    def __init__(self):
        super().__init__()

    def calculate_metric(self, data: Dict[str, Any]):
        # Fetch performance claims info
        self.score = 0.0

