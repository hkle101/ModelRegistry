"""Data fetcher for the Bus Factor metric.

This module pulls evidence from GitHub/Hugging Face sources and normalizes it
into a dict shape expected by the bus factor scoring logic.
"""

import os
from typing import Any, Dict, List, Optional, Set
import requests
from .basemetricdata_fetcher import BaseDataFetcher


# GitHub commits API template. We'll request a page of commits (per_page up to 100).
_GH_COMMITS_API = "https://api.github.com/repos/{repo}/commits?per_page={per_page}"


class BusFactorDataFetcher(BaseDataFetcher):
    """Fetches evidence needed for Bus Factor metric.

    Output shape:
      { "commit_authors": List[str] }

    Sources handled:
      - GitHub repo metadata (fetch_Codedata): use commits API to collect authors
      - HF model/dataset metadata (fetch_Modeldata/fetch_Datasetdata):
          attempt to discover a linked GitHub repo from README and query it
    """

    def __init__(self):
        super().__init__()

    # -------------------------
    # Public fetcher overrides
    # -------------------------
    def fetch_Codedata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract commit authors for a GitHub repository.

        Expects a GitHub repo metadata dict (https://api.github.com/repos/{owner}/{repo}).
        We'll derive owner/repo from the "full_name" field and query the commits API.
        """
        repo_full_name = str(data.get("full_name", "") or "").strip()
        if not repo_full_name:
            return {"commit_authors": []}

        authors = self._fetch_commit_authors_from_github(repo_full_name, per_page=100)
        unique_authors = self._unique_preserve_order(authors)
        return {"commit_authors": unique_authors}

    def fetch_Modeldata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to find a linked GitHub repo for a Hugging Face model and fetch authors."""
        # Try README of the HF model repo to locate a GitHub repo reference
        model_id = str(data.get("id", "") or data.get("modelId", "") or "").strip()
        if model_id:
            readme = self._fetch_hf_readme(model_id, kind="model")
            repo = self._extract_github_repo_from_text(readme or "") if readme else None
            if repo:
                authors = self._fetch_commit_authors_from_github(repo, per_page=100)
                return {"commit_authors": self._unique_preserve_order(authors)}
        # If no repo found, return empty list
        return {"commit_authors": []}

    def fetch_Datasetdata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to find a linked GitHub repo for a Hugging Face dataset and fetch authors."""
        ds_id = str(data.get("id", "") or "").strip()
        if ds_id:
            readme = self._fetch_hf_readme(ds_id, kind="dataset")
            repo = self._extract_github_repo_from_text(readme or "") if readme else None
            if repo:
                authors = self._fetch_commit_authors_from_github(repo, per_page=100)
                return {"commit_authors": self._unique_preserve_order(authors)}
        return {"commit_authors": []}

    # -------------------------
    # Internal helpers
    # -------------------------
    def _make_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
        return headers

    def _fetch_commit_authors_from_github(
        self, repo_path: str, per_page: int = 100
    ) -> List[str]:
        """Fetch recent commits from GitHub and return a list of author identifiers.

        We attempt to use the user login from the top-level "author.login" when present;
        otherwise we fall back to the commit author name/email from the commit payload.
        The returned list may include duplicates; the caller should uniquify if needed.
        """
        try:
            url = _GH_COMMITS_API.format(repo=repo_path, per_page=per_page)
            resp = requests.get(url, headers=self._make_headers(), timeout=10)
            if resp.status_code != 200:
                return []
            commits = resp.json() or []
            authors: List[str] = []
            for c in commits:
                a = c.get("author")
                if isinstance(a, dict) and a.get("login"):
                    authors.append(str(a["login"]))
                    continue
                commit_info = (c.get("commit") or {}).get("author", {})
                name = commit_info.get("name")
                email = commit_info.get("email")
                if name:
                    authors.append(str(name))
                elif email:
                    authors.append(str(email))
            return authors
        except Exception:
            return []

    def _unique_preserve_order(self, items: List[str]) -> List[str]:
        seen: Set[str] = set()
        out: List[str] = []
        for it in items or []:
            key = (str(it) if it is not None else "").strip()
            if key and key not in seen:
                seen.add(key)
                out.append(key)
        return out

    def _fetch_hf_readme(self, identifier: str, kind: str) -> Optional[str]:
        """Fetch README.md raw contents from a Hugging Face model or dataset.

        kind: "model" or "dataset"
        """
        if not identifier:
            return None
        base = "https://huggingface.co"
        if kind == "dataset":
            url = f"{base}/datasets/{identifier}/resolve/main/README.md"
        else:
            url = f"{base}/{identifier}/resolve/main/README.md"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and isinstance(resp.text, str):
                return resp.text
        except Exception:
            return None
        return None

    def _extract_github_repo_from_text(self, text: str) -> Optional[str]:
        """Extract first GitHub owner/repo from a README or text blob.

        Returns value like "owner/repo" or None.
        """
        if not text:
            return None
        marker = "github.com/"
        idx = text.find(marker)
        if idx == -1:
            return None
        frag = text[idx + len(marker) : idx + len(marker) + 200]
        for delim in [" ", "\n", "\r", "\t", ")", "]", "<", ">", '"', "'", "#"]:
            frag = frag.split(delim)[0]
        parts = frag.strip().split("/")
        if len(parts) >= 2:
            owner = parts[0]
            repo = parts[1].rstrip(".,);]\n\r")
            if owner and repo:
                return f"{owner}/{repo}"
        return None