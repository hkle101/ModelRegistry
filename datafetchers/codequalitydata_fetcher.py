"""Fetch code quality related metadata (tests, CI, lint presence).

This is a simplified placeholder implementation that returns a small, fixed
structure used by the `metrics.codequality` metric during scaffolding. Replace
with more advanced GitHub/HF API logic as needed.
"""

from typing import Dict, Any

from .basemetricdata_fetcher import BaseDataFetcher


class CodeQualityDataFetcher(BaseDataFetcher):
    """Return simplified code-quality signals for a model/repo."""

    def fetch_Modeldata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "has_tests": False,
            "has_ci": False,
            "has_lint_config": False,
            "language_counts": {},
            "total_code_files": 0,
            "has_readme": False,
            "has_packaging": False,
        }

    def fetch_Codedata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        return self.fetch_Modeldata(metadata)

    def fetch_Datasetdata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        return self.fetch_Modeldata(metadata)
