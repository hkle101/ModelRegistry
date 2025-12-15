"""High-level artifact management helpers for the CLI.

This module provides ArtifactManager, which orchestrates metadata
fetching, metric data preparation, and scoring for a single artifact
URL.
"""

from typing import Dict, Any
import re
import logging
import uuid

try:
    from ModelRegistry.cli.utils.MetadataFetcher import MetadataFetcher
    from ModelRegistry.cli.utils.MetricScorer import MetricScorer
    from ModelRegistry.cli.utils.MetricDataFetcher import MetricDataFetcher
except ModuleNotFoundError:  # fallback when running inside ModelRegistry
    from cli.utils.MetadataFetcher import MetadataFetcher
    from cli.utils.MetricScorer import MetricScorer
    from cli.utils.MetricDataFetcher import MetricDataFetcher

logger = logging.getLogger(__name__)


class ArtifactManager:
    """Manager to score and store artifacts (models, datasets, code)."""

    def __init__(self) -> None:
        self.metadatafetcher = MetadataFetcher()
        self.metricdatafetcher = MetricDataFetcher()
        self.scorer = MetricScorer()

    def _extract_name_from_url(self, url: str) -> str:
        """Extract a clean artifact name from a URL."""
        path_part = url.rstrip("/").split("/")[-1]
        name = re.sub(r"[^\w\-\.]", "_", path_part).replace(".git", "")
        return name or "unknown_artifact"

    def getArtifactData(self, url: str) -> Dict[str, Any]:
        """Fetch metadata and structured data for an artifact."""
        meta_info = self.metadatafetcher.fetch(url)
        artifact_data = self.metricdatafetcher.fetch_artifact_data(meta_info)
        return artifact_data

    def scoreArtifact(self, artifact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score artifact using all metrics."""
        scores = self.scorer.score_artifact(artifact_data)
        return scores

    def processUrl(self, url: str) -> Dict[str, Any]:
        """Fetch, score, and return artifact data and scores for a given URL with unique ID."""
        artifact_id = uuid.uuid4().hex  # generate unique artifact ID
        name = self._extract_name_from_url(url)

        artifact_data = self.getArtifactData(url)
        scores = self.scoreArtifact(artifact_data)

        artifact_data.update(
            {"artifact_id": artifact_id, "name": name, "scores": scores}
        )

        logger.info(f"Processed artifact {name} ({artifact_id}) from URL: {url}")
        return artifact_data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example URL to test
    test_url = "https://github.com/hkle101/ModelRegistry"

    manager = ArtifactManager()
    result = manager.processUrl(test_url)

    print("Processed Artifact Data:")
    for key, value in result.items():
        print(f"{key}: {value}")
