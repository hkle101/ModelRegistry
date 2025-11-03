from typing import Dict, Any, Optional
import json
import re
import logging

from cli.utils.MetadataFetcher import MetadataFetcher
from cli.utils.MetricScorer import MetricScorer
from cli.utils.MetricDataFetcher import MetricDataFetcher
from aws.s3_helper import upload_model_metadata, get_model_metadata, delete_model_metadata, list_models

class ModelManager:
    """Manager to score models/datasets/repos using MetadataFetcher, MetricDataFetcher, and MetricScorer.
       Provides ScoreModel API and S3 storage for metadata.
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

    def ScoreModel(self, model_url: str, name: Optional[str] = None, out_path: Optional[str] = None) -> Dict[str, Any]:
        """Fetch metadata, extract metrics, score them, and return a dict."""
        if not name:
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
            "Scores": scores,
        }

        if out_path:
            try:
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
            except Exception:
                self.logger.exception("Failed to write result to %s", out_path)

        return result

    # ------------------------
    # S3 Metadata Operations
    # ------------------------

    def SaveModelMetadata(self, score_dict: Dict[str, Any]) -> str:
        """
        Upload ScoreModel output to S3.
        Returns S3 path of uploaded JSON.
        """
        model_name = score_dict.get("Name", "unknown_model")
        scores = score_dict.get("Scores", {})
        url = score_dict.get("url", "")

        s3_path = upload_model_metadata(model_name, scores, url)
        self.logger.info(f"Uploaded model metadata to {s3_path}")
        return s3_path

    def GetModelMetadata(self, model_name: str) -> dict:
        """Retrieve a model's metadata JSON from S3."""
        return get_model_metadata(model_name)

    def DeleteModelMetadata(self, model_name: str) -> None:
        """Delete a model's metadata JSON from S3."""
        delete_model_metadata(model_name)

    def ListModels(self) -> list:
        """List all model names stored in S3."""
        return list_models()

def main():
    """Command-line helper to test ModelManager quickly."""
    mgr = ModelManager()
    test_url = "https://huggingface.co/bert-base-uncased"
    res = mgr.ScoreModel(test_url)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
