"""License scoring metric implementation."""

from typing import Any, Dict
from .basemetric import BaseMetric
try:
    from ModelRegistry.datafetchers.licensedata_fetcher import LicenseDataFetcher
except ModuleNotFoundError:
    from datafetchers.licensedata_fetcher import LicenseDataFetcher


class LicenseMetric(BaseMetric):
    """
    Scores the license quality of a model, dataset, or repository.
    License quality is categorized into four tiers:
        - High quality (score = 1.0)
        - Medium quality (score = 0.75)
        - Custom (score = 0.5)
        - Unknown (score = 0.2)
    """

    def __init__(self):
        super().__init__()
        self.datafetcher = LicenseDataFetcher()

    def calculate_metric(self, data: Dict[str, Any]):
        # Fetch license info
        license_name = data.get("license", "unknown").lower()
        # Define license categories
        high_quality = [
            "mit", "apache-2.0", "bsd-3-clause", "bsd-2-clause",
            "cc0", "cc0-1.0", "isc", "zlib", "unlicense"
        ]
        medium_quality = [
            "mpl-2.0", "lgpl-3.0", "cc-by-4.0", "cc-by-sa-4.0", "epl-2.0",
            "artistic-2.0", "agpl-3.0", "openrail"
        ]
        # Determine score
        if license_name == "custom":
            self.score = 0.5
        elif license_name == "unknown":
            self.score = 0.0
        elif any(key in license_name for key in high_quality):
            self.score = 1.0
        elif any(key in license_name for key in medium_quality):
            self.score = 0.75
        else:
            self.score = 0.4
