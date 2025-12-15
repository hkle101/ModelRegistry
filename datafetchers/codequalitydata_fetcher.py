"""Data fetcher for code-quality related signals.

This module defines CodeQualityDataFetcher, which inspects repository
trees, languages, config files, and docs to supply inputs to the
CodeQualityMetric.
"""

import os
from typing import Any, Dict, List, Optional

import requests

from .basemetricdata_fetcher import BaseDataFetcher


# GitHub trees API template to list repository files recursively
_GH_TREE_API = "https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"

# Map common file extensions to language labels
_EXT_LANG_MAP: Dict[str, str] = {
    # Python / notebooks
    ".py": "Python",
    ".ipynb": "Notebook",
    # C-family
    ".c": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C/C++ Header",
    ".cu": "CUDA",
    ".cu.h": "CUDA",
    # Java / JVM
    ".java": "Java",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".gradle": "Gradle",
    # JavaScript / TypeScript / Node
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    # Web / scripting
    ".sh": "Shell",
    ".ps1": "PowerShell",
    # R / Julia
    ".r": "R",
    ".jl": "Julia",
    # Go / Rust / C#
    ".go": "Go",
    ".rs": "Rust",
    ".cs": "C#",
    # PHP / Ruby / Swift / Objective-C / MATLAB
    ".php": "PHP",
    ".rb": "Ruby",
    ".swift": "Swift",
    ".m": "Objective-C_or_MATLAB",
    ".mm": "Objective-C++",
    # Others
    ".pl": "Perl",
    ".tex": "LaTeX",
}


class CodeQualityDataFetcher(BaseDataFetcher):
    """Fetches code-quality related evidence from metadata.

    Produces a uniform dict with these keys:
      - has_tests: bool
      - has_ci: bool
      - has_lint_config: bool
      - language_counts: Dict[str, int]
      - total_code_files: int
      - has_readme: bool
      - has_packaging: bool

    Sources handled:
      - GitHub repo metadata (fetch_Codedata): uses GitHub trees API to scan files
      - HF model/dataset metadata (fetch_Modeldata/fetch_Datasetdata): uses siblings list
    """

    def __init__(self):
        super().__init__()

    # -------------------------
    # Public fetcher overrides
    # -------------------------
    def fetch_Codedata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract evidence for a GitHub repository.

        Expects a GitHub repo metadata dict (like https://api.github.com/repos/{owner}/{repo}).
        We'll derive owner/repo from the "full_name" field and query the trees API.
        """
        self.metadata = self._empty_result()

        # Try to parse owner/repo and default branch from GitHub metadata
        repo_full_name = str(data.get("full_name", "") or "").strip()
        default_branch = str(data.get("default_branch", "") or "").strip() or "HEAD"
        if not repo_full_name:
            return self.metadata

        tree = self._fetch_repo_tree(repo_full_name, default_branch)
        if not tree:
            return self.metadata

        paths = [str(e.get("path", "") or "") for e in tree]
        self.metadata = self._aggregate_from_paths(paths)
        return self.metadata

    def fetch_Modeldata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract evidence from a Hugging Face model card metadata.

        Heuristic: use the "siblings" listing to infer presence of tests, CI, lint,
        packaging and language counts in files bundled with the model repo.
        """
        self.metadata = self._empty_result()
        siblings = data.get("siblings")
        if isinstance(siblings, list):
            paths = [
                str(item.get("rfilename", "") or "")
                for item in siblings
                if isinstance(item, dict)
            ]
            self.metadata = self._aggregate_from_paths(paths)
        # If HF repo is sparse (common for pure model repos), attempt to find a linked
        # GitHub repository in README.md and aggregate from its tree.
        if self._looks_sparse(self.metadata):
            model_id = str(data.get("id", "") or data.get("modelId", "") or "").strip()
            if model_id:
                readme = self._fetch_hf_readme(model_id, kind="model")
                repo = (
                    self._extract_github_repo_from_text(readme or "")
                    if readme
                    else None
                )
                if repo:
                    tree = self._fetch_repo_tree(repo, "HEAD")
                    if tree:
                        paths = [str(e.get("path", "") or "") for e in tree]
                        self.metadata = self._aggregate_from_paths(paths)
        return self.metadata

    def fetch_Datasetdata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract evidence from a Hugging Face dataset metadata (same heuristic as model)."""
        self.metadata = self._empty_result()
        siblings = data.get("siblings")
        if isinstance(siblings, list):
            paths = [
                str(item.get("rfilename", "") or "")
                for item in siblings
                if isinstance(item, dict)
            ]
            self.metadata = self._aggregate_from_paths(paths)
        # Similar fallback for datasets: try README to locate a linked GitHub repo
        if self._looks_sparse(self.metadata):
            ds_id = str(data.get("id", "") or "").strip()
            if ds_id:
                readme = self._fetch_hf_readme(ds_id, kind="dataset")
                repo = (
                    self._extract_github_repo_from_text(readme or "")
                    if readme
                    else None
                )
                if repo:
                    tree = self._fetch_repo_tree(repo, "HEAD")
                    if tree:
                        paths = [str(e.get("path", "") or "") for e in tree]
                        self.metadata = self._aggregate_from_paths(paths)
        return self.metadata

    # -------------------------
    # Internal helpers
    # -------------------------
    def _empty_result(self) -> Dict[str, Any]:
        return {
            "has_tests": False,
            "has_ci": False,
            "has_lint_config": False,
            "language_counts": {},
            "total_code_files": 0,
            "has_readme": False,
            "has_packaging": False,
        }

    def _make_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
        return headers

    def _looks_sparse(self, meta: Dict[str, Any]) -> bool:
        """Heuristic: return True if there is little/no evidence from HF siblings.

        Consider sparse when no languages found and none of tests/ci/lint/packaging detected.
        """
        if not isinstance(meta, dict):
            return True
        lang_counts = meta.get("language_counts", {}) or {}
        return (
            len(lang_counts) == 0
            and not meta.get("has_tests", False)
            and not meta.get("has_ci", False)
            and not meta.get("has_lint_config", False)
            and not meta.get("has_packaging", False)
        )

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
        # Simple heuristic search to avoid heavy regex dependencies
        marker = "github.com/"
        idx = text.find(marker)
        if idx == -1:
            return None
        frag = text[idx + len(marker): idx + len(marker) + 200]
        # Split on delimiters that commonly follow repo paths
        for delim in [" ", "\n", "\r", "\t", ")", "]", "<", ">", '"', "'", "#"]:
            frag = frag.split(delim)[0]
        # owner/repo[/...]
        parts = frag.strip().split("/")
        if len(parts) >= 2:
            owner = parts[0]
            repo = parts[1]
            # Clean trailing punctuation
            repo = repo.rstrip(".,);]\n\r")
            if owner and repo:
                return f"{owner}/{repo}"
        return None

    def _fetch_repo_tree(
        self, repo_path: str, branch: str = "HEAD"
    ) -> Optional[List[Dict[str, Any]]]:
        url = _GH_TREE_API.format(repo=repo_path, branch=branch)
        try:
            resp = requests.get(url, headers=self._make_headers(), timeout=10)
            if resp.status_code == 200:
                payload = resp.json()
                tree = payload.get("tree", [])
                if isinstance(tree, list):
                    return tree
            return None
        except Exception:
            return None

    def _classify_by_extension(self, path: str) -> Optional[str]:
        p = path.lower()
        for ext, lang in _EXT_LANG_MAP.items():
            if p.endswith(ext):
                return lang
        return None

    def _aggregate_from_paths(self, paths: List[str]) -> Dict[str, Any]:
        has_tests = False
        has_ci = False
        has_lint_config = False
        has_readme = False
        has_packaging = False
        language_counts: Dict[str, int] = {}

        # Packaging files across ecosystems
        packaging_files = {
            "setup.py",
            "pyproject.toml",
            "setup.cfg",
            "requirements.txt",
            "package.json",
            "pom.xml",  # maven (java)
            "build.gradle",  # gradle (java/kotlin)
            "gradle.properties",
            "Cargo.toml",  # rust
            "go.mod",  # go
            "DESCRIPTION",  # R
            "environment.yml",
            "conda.yml",
            "Makefile",
            "Pipfile",
            "poetry.lock",
            "manifest.in",
            "__init__.py",
        }

        for raw_path in paths:
            path = (raw_path or "").strip().lstrip("./").lower()
            if not path:
                continue

            # Test detection (broad heuristics)
            if (
                path.startswith("tests/")
                or "/tests/" in path
                or path.startswith("test/")
                or "/test/" in path
                or path.startswith("spec/")
                or "/spec/" in path
                or path.startswith("example/")
                or "/example/" in path
                or path.startswith("examples/")
                or "/examples/" in path
                or path.startswith("test_")
                or "/test_" in path
                or path.endswith("_test.py")
                or path.endswith("test.py")
                or path.endswith("_spec.rb")
                or path.endswith(".spec.js")
                or path.endswith(".test.js")
                or "unittest" in path
                or "pytest" in path
            ):
                has_tests = True

            # CI detection
            if (
                path.startswith(".github/workflows")
                or path.endswith(".travis.yml")
                or path.endswith("travis.yml")
                or ".circleci/" in path
                or path.endswith("azure-pipelines.yml")
                or path.endswith("azure-pipelines.yaml")
                or path.endswith("jenkinsfile")
                or path.endswith("drone.yml")
                or (
                    path.endswith(".yml")
                    and ("ci" in path or "build" in path or "deploy" in path)
                )
                or (
                    path.endswith(".yaml")
                    and ("ci" in path or "build" in path or "deploy" in path)
                )
                or path.startswith("ci/")
                or "/ci/" in path
                or path == "makefile"
                or path == "dockerfile"
                or path.endswith("build.sh")
                or path.endswith("build.bat")
            ):
                has_ci = True

            # Linting / formatting detection
            if (
                path
                in {
                    ".flake8",
                    "pyproject.toml",
                    "setup.cfg",
                    "tox.ini",
                    ".pylintrc",
                    "pylint.cfg",
                    ".black",
                    ".isort.cfg",
                    ".pre-commit-config.yaml",
                    ".pre-commit-config.yml",
                    "requirements-dev.txt",
                    "requirements.dev.txt",
                    ".eslintrc",
                    ".eslintrc.json",
                    ".eslintrc.js",
                    ".eslintrc.yaml",
                    ".stylelintrc",
                    ".rubocop.yml",
                    "ruff.toml",
                }
                or path.endswith("lint.py")
                or path.endswith("format.py")
                or "linting" in path
                or "formatting" in path
            ):
                has_lint_config = True

            # README detection
            if (
                path.startswith("readme")
                or path in {"readme.md", "readme.rst", "readme.txt", "readme"}
                or path == "index.md"
                or path == "home.md"
            ):
                has_readme = True

            # Packaging detection
            if path in {p.lower() for p in packaging_files} or any(
                path.endswith(f.lower()) for f in packaging_files
            ):
                has_packaging = True

            # Language classification
            lang = self._classify_by_extension(path)
            if lang:
                language_counts[lang] = language_counts.get(lang, 0) + 1

        total_code_files = sum(language_counts.values())

        return {
            "has_tests": has_tests,
            "has_ci": has_ci,
            "has_lint_config": has_lint_config,
            "language_counts": language_counts,
            "total_code_files": total_code_files,
            "has_readme": has_readme,
            "has_packaging": has_packaging,
        }