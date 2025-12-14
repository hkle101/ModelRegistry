from typing import Any, Dict
from .basemetric import BaseMetric
import time


class SizeScoreMetric(BaseMetric):
    """
    Scores model size compatibility with different hardware.
    Stores individual device scores and measures latency.
    """

    def __init__(self):
        super().__init__()
        # Max supported model size in MB for each device
        self.device_limits_mb = {
            "raspberry_pi": 100,
            "jetson_nano": 200,
            "desktop_pc": 8000,
            "aws_server": 50000
        }
        # Initialize individual scores
        self.raspberry_pi_score: float = 0.0
        self.jetson_nano_score: float = 0.0
        self.desktop_pc_score: float = 0.0
        self.aws_server_score: float = 0.0

    def calculate_metric(self, data: Dict[str, Any]):
        """
        Calculate individual device scores based on model size.
        Scores are between 0–1. Resets previous scores at start.
        """
        # Reset scores
        self.raspberry_pi_score = 0.0
        self.jetson_nano_score = 0.0
        self.desktop_pc_score = 0.0
        self.aws_server_score = 0.0

        model_size = data.get("model_size_mb")

        if model_size == "unknown" or model_size is None:
            return  # keep all scores as 0

        try:
            model_size_val = float(model_size)
        except (TypeError, ValueError):
            return

        if model_size_val <= 0:
            return

        # Calculate score for each device. Use a small floor (0.1) so that
        # very large models are not punished with near-zero scores.
        def _device_score(limit_mb: int) -> float:
            raw = limit_mb / model_size_val
            return round(min(1.0, max(0.1, raw)), 2)

        self.raspberry_pi_score = _device_score(self.device_limits_mb["raspberry_pi"])
        self.jetson_nano_score = _device_score(self.device_limits_mb["jetson_nano"])
        self.desktop_pc_score = _device_score(self.device_limits_mb["desktop_pc"])
        self.aws_server_score = _device_score(self.device_limits_mb["aws_server"])

    def getScores(self, data: Dict[str, Any]) -> Dict[str, any]:
        """
        Calculate metric, measure latency, and return them
        """
        start_time = time.time()
        self.calculate_metric(data)
        end_time = time.time()

        # Measure latency (ms) and round to 2 decimals for consistent storage
        self.latency = round((end_time - start_time) * 1000.0, 2)
        self.raspberry_pi_score = round(self.raspberry_pi_score, 2)
        self.jetson_nano_score = round(self.jetson_nano_score, 2)
        self.desktop_pc_score = round(self.desktop_pc_score, 2)
        self.aws_server_score = round(self.aws_server_score, 2)

        # Return already-rounded scores and the rounded latency
        return {
            "raspberry_pi": self.raspberry_pi_score,
            "jetson_nano": self.jetson_nano_score,
            "desktop_pc": self.desktop_pc_score,
            "aws_server": self.aws_server_score,
            "latency": self.latency,
        }
