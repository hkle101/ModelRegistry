"""Code quality metric implementation.

This module defines CodeQualityMetric, which scores the presence of
tests, CI, linting, packaging, language diversity, and repository size.
"""

from typing import Any, Dict

# BaseMetric via relative import works in both contexts
from .basemetric import BaseMetric

# DataFetcher: support both package and top-level execution
try:
    from ModelRegistry.datafetchers.codequalitydata_fetcher import CodeQualityDataFetcher
except ModuleNotFoundError:
    from datafetchers.codequalitydata_fetcher import CodeQualityDataFetcher


class CodeQualityMetric(BaseMetric):
    """Scores code quality using evidence from CodeQualityDataFetcher.

    Expected input data keys (from fetcher):
      - has_tests: bool
      - has_ci: bool
      - has_lint_config: bool
      - language_counts: Dict[str, int]
      - total_code_files: int
      - has_readme: bool
      - has_packaging: bool

    Scoring weights (more generous for partial setups):
      - tests presence:        0.25
      - CI presence:           0.20
      - lint config:           0.10
      - code files (scaled):   0.25  (s_code = min(1.0, total_code_files/20.0))
        + diversity bonus: min(0.2, (num_languages/5.0)*0.2)
      - docs/packaging:        0.20  (1.0 if both, 0.5 if one, 0.0 if none)
    """

    def __init__(self):
        super().__init__()
        self.datafetcher = CodeQualityDataFetcher()

    def calculate_metric(self, data: Dict[str, Any]):
        has_tests = bool(data.get("has_tests", False))
        has_ci = bool(data.get("has_ci", False))
        has_lint = bool(data.get("has_lint_config", False))
        lang_counts: Dict[str, int] = data.get("language_counts", {}) or {}
        total_files = int(data.get("total_code_files", 0) or 0)
        has_readme = bool(data.get("has_readme", False))
        has_packaging = bool(data.get("has_packaging", False))

        # weights (sum to 1.0, but give more credit for structure/docs)
        w_tests, w_ci, w_lint, w_code, w_doc_pack = 0.25, 0.20, 0.10, 0.25, 0.20

        # subscores
        s_tests = 1.0 if has_tests else 0.0
        s_ci = 1.0 if has_ci else 0.0
        s_lint = 1.0 if has_lint else 0.0

        # code files subscore: scale to 20 files as "full" (more generous)
        s_code = min(1.0, total_files / 20.0) if total_files > 0 else 0.0

        # Diversity bonus (max 0.2 added to code subscore before weighting)
        num_langs = len([lang for lang, count in lang_counts.items() if count > 0])
        diversity_bonus = min(0.2, (num_langs / 5.0) * 0.2) if num_langs > 0 else 0.0
        s_code = min(1.0, s_code + diversity_bonus)

        # docs/packaging score
        if has_readme and has_packaging:
            s_doc_pack = 1.0
        elif has_readme or has_packaging:
            s_doc_pack = 0.5
        else:
            s_doc_pack = 0.0

        score = (
            w_tests * s_tests
            + w_ci * s_ci
            + w_lint * s_lint
            + w_code * s_code
            + w_doc_pack * s_doc_pack
        )

        # clamp to [0,1]
        self.score = max(0.0, min(1.0, float(score)))