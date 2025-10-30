# fetcher/metadata_fetcher.py
import requests
import os
from urllib.parse import urlparse


class MetadataFetcher:
    """
    MetadataFetcher retrieves full metadata from Hugging Face models,
    Hugging Face datasets, or GitHub repositories.
    """

    def __init__(self, github_token=None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.headers = {"Authorization": f"token {self.github_token}"} if self.github_token else {}

    def fetch(self, url: str):
        """
        Determine the type of URL and call the appropriate metadata fetcher.
        Returns:
            dict: The full metadata as returned by the API.
        """
        if "huggingface.co" in url:
            if "/datasets/" in url:
                return self._fetch_hf_dataset_metadata(url)
            else:
                return self._fetch_hf_model_metadata(url)
        elif "github.com" in url:
            return self._fetch_github_metadata(url)
        else:
            raise ValueError(f"Unsupported URL: {url}")

    def _fetch_metadata(self, api_url: str):
        """Generic method to fetch metadata from a given API URL."""
        response = requests.get(api_url, headers=self.headers)
        response.raise_for_status()
        return response.json()  # Return full raw metadata

    def _fetch_hf_model_metadata(self, url: str):
        """Fetch full Hugging Face model metadata."""
        model_id = urlparse(url).path.strip("/")
        api_url = f"https://huggingface.co/api/models/{model_id}"
        return self._fetch_metadata(api_url)

    def _fetch_hf_dataset_metadata(self, url: str):
        """Fetch full Hugging Face dataset metadata."""
        dataset_id = urlparse(url).path.split("/datasets/")[-1]
        api_url = f"https://huggingface.co/api/datasets/{dataset_id}"
        return self._fetch_metadata(api_url)

    def _fetch_github_metadata(self, url: str):
        """Fetch full GitHub repository metadata."""
        path = urlparse(url).path.strip("/")
        owner, repo = path.split("/")[:2]
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(api_url, headers=self.headers)
        response.raise_for_status()
        return response.json()  # Return full raw metadata


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Fetch metadata for a model, dataset, or GitHub repo URL")
    parser.add_argument("url", type=str, help="URL of the model, dataset, or GitHub repository")
    parser.add_argument("--github-token", type=str, default=None, help="GitHub token if needed for private repos")
    args = parser.parse_args()

    fetcher = MetadataFetcher(github_token=args.github_token)

    try:
        metadata = fetcher.fetch(args.url)

        # Save metadata to model.txt in the repo
        repo_dir = os.path.dirname(os.path.abspath(__file__))  # directory of this script
        file_path = os.path.join(repo_dir, "model.txt")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)

        print(f"Metadata saved to {file_path}")

    except Exception as e:
        print(f"Error fetching metadata: {e}")
