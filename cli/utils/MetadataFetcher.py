"""Metadata fetching helpers.

Fetches and normalizes metadata for Hugging Face (models/datasets) and GitHub
repositories, including a suitable download URL when available.
"""

import requests
from urllib.parse import urlparse
import logging
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MetadataFetcher:
    """
    Retrieves metadata from Hugging Face or GitHub.
    Returns a dictionary including:
      - 'artifact_type'
      - 'download_url'
      - other metadata fields
    """

    def __init__(self, github_token: str = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.headers = {"Authorization": f"token {self.github_token}"} if self.github_token else {}

    def fetch(self, url: str) -> dict:
        """
        Determine artifact type, fetch metadata, and add download URL.
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
            data["download_url"] = self.get_download_url(url, data)

            return data

        except Exception as e:
            logger.exception("Failed to fetch metadata for URL: %s", url)
            return {"artifact_type": "unknown", "error": str(e), "download_url": None}

    def get_download_url(self, url: str, metadata: dict | None) -> str | None:
        """
        Return a direct download URL if possible.
        """
        if not metadata:
            return None

        # ---------- GitHub ----------
        if "github.com" in url:
            path = urlparse(url).path.strip("/")
            owner, repo = path.split("/")[:2]
            return f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"

        # ---------- Hugging Face ----------
        if "huggingface.co" in url:
            # Dataset download
            if "/datasets/" in url:
                dataset_id = urlparse(url).path.split("/datasets/")[-1].strip("/")
                return f"https://huggingface.co/datasets/{dataset_id}/resolve/main/{dataset_id}.zip"

            # Model download
            repo_id = metadata.get("modelId") or metadata.get("id")
            siblings = metadata.get("siblings", [])

            preferred_files = [
                "model.safetensors",
                "pytorch_model.bin",
                "tf_model.h5",
                "flax_model.msgpack",
            ]

            for file in preferred_files:
                if any(s.get("rfilename") == file for s in siblings):
                    return f"https://huggingface.co/{repo_id}/resolve/main/{file}"

        return None

    # ----- Internal fetch helpers -----
    def _fetch_metadata(self, api_url: str) -> dict:
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
            dataset_id = urlparse(url).path.split("/datasets/")[-1].strip("/")
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
    url = input("Enter a model/dataset/repo URL: ").strip()
    fetcher = MetadataFetcher()
    result = fetcher.fetch(url)

    print("\n=== MetadataFetcher Result ===")
    print("artifact_type:", result.get("artifact_type"))
    print("download_url:", result.get("download_url"))
