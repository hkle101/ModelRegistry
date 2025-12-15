"""Core metric base class and timing helper utilities.

This module defines the abstract BaseMetric used by all concrete
metric implementations and provides consistent latency measurement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
import time


class BaseMetric(ABC):
    """
    Abstract base class for all metric types.
    Provides timing and score storage.
    """

    def __init__(self):
        # Internal storage; outputs are converted to Decimal
        self.score: float = 0.00
        self.latency: float = 0.00

    @abstractmethod
    def calculate_metric(self, data: Dict[str, Any]):
        """
        Abstract method to calculate the metric based on provided data.
        Must be implemented by all subclasses.
        Should return the calculated score.
        """
        pass

    def getScores(self, data: Dict[str, Any]) -> Dict[str, any]:
        """
        Calculates the metric and measures its latency.
        Returns both the score and latency.
        """
        # Use a high-resolution timer so very fast metrics still
        # report a meaningful non-zero latency when appropriate.
        start_time = time.perf_counter()
        # Run the actual metric calculation
        self.calculate_metric(data)
        end_time = time.perf_counter()
        # Compute latency in milliseconds and round values to 2 decimals
        self.latency = round((end_time - start_time) * 1000.0, 2)
        self.score = round(float(self.score), 2)
        return {
            "score": self.score,
            "latency": self.latency,
        }
