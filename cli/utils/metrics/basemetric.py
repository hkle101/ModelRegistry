from abc import ABC, abstractmethod
from typing import Any, Dict
import time


class BaseMetric(ABC):
    """
    Abstract base class for all metric types.
    Provides timing and score storage.
    """

    def __init__(self):
        self.score: float = 0.0
        self.latency: float = 0.0

    @abstractmethod
    def calculate_metric(self, data: Dict[str, Any]):
        """
        Abstract method to calculate the metric based on provided data.
        Must be implemented by all subclasses.
        Should return the calculated score.
        """
        pass

    def getScores(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculates the metric and measures its latency.
        Returns both the score and latency.
        """
        start_time = time.time()
        # Run the actual metric calculation
        self.calculate_metric(data)
        end_time = time.time()
        # Compute latency in milliseconds
        self.latency = (end_time - start_time) * 1000.0
        return {
            "score": self.score,
            "latency": self.latency
        }
