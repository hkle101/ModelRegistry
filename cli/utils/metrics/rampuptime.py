from typing import Any, Dict
from cli.utils.metrics.basemetric import BaseMetric


class RampUpTimeMetric(BaseMetric):
    """
    Class for scoring Ramp Up Time Metric
    """

    def __init__(self):
        super().__init__()

    def calculate_metric(self, data: Dict[str, Any]):
        # Fetch ramp-up time info
        self.score = 0.0
