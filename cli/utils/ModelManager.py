from typing import Dict, Any, Optional
import json
import re
import logging

from cli.utils.MetadataFetcher import MetadataFetcher
from cli.utils.MetricScorer import MetricScorer
from cli.utils.MetricDataFetcher import MetricDataFetcher


class ModelManager:
    """Manager to score models/datasets/repos using the repository's
    MetadataFetcher, MetricDataFetcher, and MetricScorer.

    Public API:
      - ScoreModel(model_url: str) -> str: JSON content (does not save to file)
    """

    def __init__(self) -> None:
        self.metadata_fetcher = MetadataFetcher()
        self.metric_data_fetcher = MetricDataFetcher()
        self.scorer = MetricScorer()
        self.logger = logging.getLogger(__name__)

    def _extract_name_from_url(self, model_url: str) -> str:
        """Extract a clean model name from the given URL."""
        path_part = model_url.rstrip("/").split("/")[-1]
        name = re.sub(r"[^\w\-\.]", "_", path_part).replace(".git", "")
        return name or "unknown_model"

    def ScoreModel(self, model_url: str) -> str:
        """Fetch metadata, extract metrics, score them, and return JSON content."""
        name = self._extract_name_from_url(model_url)
        self.logger.info(f"Scoring model: {name} ({model_url})")

        # Fetch raw metadata
        try:
            raw_meta = self.metadata_fetcher.fetch(model_url)
        except Exception as e:
            self.logger.exception("Metadata fetch failed for %s", model_url)
            raw_meta = {"_metadata_fetch_error": str(e)}

        # Extract model data
        try:
            modeldata = self.metric_data_fetcher.fetch_from_metadata(raw_meta)
        except Exception as e:
            self.logger.exception("Metric data extraction failed for %s", model_url)
            modeldata = {"_metricdata_fetch_error": str(e)}

        # Score metrics
        try:
            scores = self.scorer.score_all_metrics(modeldata)
        except Exception as e:
            self.logger.exception("Metric scoring failed for %s", model_url)
            scores = {"_metricscorer_error": str(e)}

        # Combine results
        result: Dict[str, Any] = {
            "Name": name,
            "url": model_url,
            "scores": scores,
        }

        # Convert to JSON string
        json_content = json.dumps(result, indent=2)
        return json_content

    @staticmethod
    def main():
        """Example main method to run ModelManager and print JSON content."""
        manager = ModelManager()
        test_url = "https://huggingface.co/bert-base-uncased"  # Replace with any model URL
        json_result = manager.ScoreModel(test_url)

        print("\n=== JSON Output ===")
        print(json_result)


if __name__ == "__main__":
    ModelManager.main()
