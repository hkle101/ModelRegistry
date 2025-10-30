from abc import ABC, abstractmethod
from typing import Any, Dict
from cli.utils.MetadataFetcher import MetadataFetcher


class BaseDataFetcher(ABC):
    """
    Abstract base class defining the contract for fetching
    data related to 8 evaluation metrics from metadata or other sources.
    Each metric method must be implemented by subclasses.
        1. License
        2. Bus Factor
        3. Code Quality
        4. Dataset and Code Score
        5. Dataset Quality
        6. Performance Claims
        7. Ramp-up Time
        8. Size
    """
    metadata: Dict[str, Any]

    def __init__(self):
        self.metadata = {}
        self.MetadataFetcher = MetadataFetcher()

    @abstractmethod
    def fetch_Modeldata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch metadata for a given URL."""
        pass

    def fetch_Codedata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch code metadata for a given URL."""
        self.metadata["code"] = data.get("code", "unknown")
        return self.metadata

    def fetch_Datasetdata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch dataset metadata for a given URL."""
        self.metadata["dataset"] = data.get("dataset", "unknown")
        return self.metadata
