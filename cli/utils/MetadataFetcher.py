import requests
from urllib.parse import urlparse
import logging
import os

logger = logging.getLogger(__name__)


class MetadataFetcher:
    """
    Retrieves metadata from Hugging Face or GitHub.
    Returns a flat dictionary that includes 'artifact_type' along with metadata fields.
    """

    def __init__(self, github_token: str = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.headers = {"Authorization": f"token {self.github_token}"} if self.github_token else {}

    def fetch(self, url: str) -> dict:
        """
        Determine artifact type and safely fetch metadata.
        Returns a dictionary with 'artifact_type' merged into the metadata.
        """
        try:
            if "huggingface.co" in url:
                if "/datasets/" in url:
                    metadata = self._fetch_hf_dataset_metadata(url)
                    metadata["artifact_type"] = "dataset"
                else:
                    metadata = self._fetch_hf_model_metadata(url)
                    metadata["artifact_type"] = "model"
                return metadata

            elif "github.com" in url:
                metadata = self._fetch_github_metadata(url)
                if "error" not in metadata:
                    metadata["artifact_type"] = "code"
                return metadata

            else:
                logger.warning("Unsupported URL format: %s", url)
                return {"artifact_type": "unknown", "error": "Unsupported URL format"}

        except Exception as e:
            logger.exception("Failed to fetch metadata for URL: %s", url)
            return {"artifact_type": "unknown", "error": str(e)}

    def _fetch_metadata(self, api_url: str) -> dict:
        """Generic safe fetch with logging."""
        try:
            response = requests.get(api_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            logger.info("Fetched metadata from %s", api_url)
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error("HTTPError fetching metadata from %s: %s", api_url, e)
            return {"error": f"HTTPError: {e}"}
        except requests.exceptions.Timeout:
            logger.error("Timeout fetching metadata from %s", api_url)
            return {"error": "Timeout"}
        except requests.exceptions.RequestException as e:
            logger.exception("RequestException fetching metadata from %s", api_url)
            return {"error": f"RequestException: {e}"}
        except Exception as e:
            logger.exception("Unexpected error fetching metadata from %s", api_url)
            return {"error": f"UnexpectedError: {e}"}

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
                logger.warning("GitHub URL invalid, must include owner/repo: %s", url)
                return {"artifact_type": "unknown", "error": "GitHub URL must include owner and repository name"}
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

