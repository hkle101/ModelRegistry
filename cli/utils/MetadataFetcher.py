"""Metadata fetching helpers for Hugging Face and GitHub artifacts.

This module defines MetadataFetcher, which discovers artifact type,
pulls raw metadata via the appropriate API, and computes a convenient
download URL.
"""

import requests
from urllib.parse import urlparse
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class MetadataFetcher:
    """
    Retrieves metadata from Hugging Face or GitHub.
    Returns a flat dictionary that includes:
      - 'artifact_type'
      - 'download_url'
      - metadata fields
    """

    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.headers = {"Authorization": f"token {self.github_token}"} if self.github_token else {}

    def fetch(self, url: str) -> dict:
        """
        Determine artifact type, fetch metadata, and add download URL.
        Returns a dictionary with 'artifact_type' and 'download_url'.
        """
        try:
            data: dict = {}

            if "huggingface.co" in url:
                if "/datasets/" in url:
                    data = self._fetch_hf_dataset_metadata(url)
                    data["artifact_type"] = "dataset"
                else:
                    data = self._fetch_hf_model_metadata(url)
                    data["artifact_type"] = "model"

            elif "github.com" in url:
                data = self._fetch_github_metadata(url)
                if "error" not in data:
                    data["artifact_type"] = "code"

            else:
                logger.warning("Unsupported URL format: %s", url)
                data = {"artifact_type": "unknown", "error": "Unsupported URL format"}

            # Add download URL
            data["download_url"] = self.get_download_url(url)

            return data

        except Exception as e:
            logger.exception("Failed to fetch metadata for URL: %s", url)
            return {"artifact_type": "unknown", "error": str(e), "download_url": None}

    def get_download_url(self, url: str) -> str | None:
        """
        Returns a direct download URL for the artifact, if possible.
        Supports GitHub repos, Hugging Face models, and datasets.
        """
        try:
            if "github.com" in url:
                path = urlparse(url).path.strip("/")
                parts = path.split("/")
                if len(parts) >= 2:
                    owner, repo = parts[:2]
                    return f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"
                return None

            elif "huggingface.co" in url:
                path = urlparse(url).path.strip("/")
                if "/datasets/" in path:
                    dataset_id = path.split("/datasets/")[-1]
                    return f"https://huggingface.co/datasets/{dataset_id}/resolve/main/{dataset_id}.zip"
                else:
                    model_id = path
                    return f"https://huggingface.co/{model_id}/resolve/main/{model_id}.zip"

            else:
                logger.warning("Unsupported URL for download: %s", url)
                return None

        except Exception as e:
            logger.exception("Failed to generate download URL for %s: %s", url, e)
            return None

    # ----- Internal fetch helpers -----
    def _fetch_metadata(self, api_url: str) -> dict:
        """Generic safe fetch with logging."""
        try:
            response = requests.get(api_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            logger.info("Fetched metadata from %s", api_url)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.exception("Failed to fetch metadata from %s: %s", api_url, e)
            return {"error": str(e)}

    def _fetch_hf_model_metadata(self, url: str) -> dict:
        try:
            model_id = urlparse(url).path.strip("/")
            api_url = f"https://huggingface.co/api/models/{model_id}"
            return self._fetch_metadata(api_url)
        except Exception as e:
            logger.exception("Failed to fetch Hugging Face model metadata: %s", url)
            return {"error": str(e)}

    def _fetch_hf_dataset_metadata(self, url: str) -> dict:
        try:
            dataset_id = urlparse(url).path.split("/datasets/")[-1]
            api_url = f"https://huggingface.co/api/datasets/{dataset_id}"
            return self._fetch_metadata(api_url)
        except Exception as e:
            logger.exception("Failed to fetch Hugging Face dataset metadata: %s", url)
            return {"error": str(e)}

    def _fetch_github_metadata(self, url: str) -> dict:
        try:
            path = urlparse(url).path.strip("/")
            parts = path.split("/")
            if len(parts) < 2:
                return {"artifact_type": "unknown", "error": "GitHub URL must include owner/repo"}
            owner, repo = parts[:2]
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            return self._fetch_metadata(api_url)
        except Exception as e:
            logger.exception("Failed to fetch GitHub metadata: %s", url)
            return {"artifact_type": "unknown", "error": str(e)}


if __name__ == "__main__":
    # Example URLs to test:
    # HF model: https://huggingface.co/gpt2
    # HF dataset: https://huggingface.co/datasets/imagenet-1k
    # GitHub repo: https://github.com/psf/requests

    url = input("Enter a model/dataset/repo URL: ").strip()

    fetcher = MetadataFetcher()
    result = fetcher.fetch(url)

    print("\n=== MetadataFetcher Result ===")
    print("artifact_type:", result.get("artifact_type"))
    print("raw_metadata:", result)