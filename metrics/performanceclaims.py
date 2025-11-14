from typing import Any, Dict
from .basemetric import BaseMetric


class PerformanceClaimsMetric(BaseMetric):
    """
    Evaluate evidence of performance claims for a given model.

    Scoring heuristics (kept similar to the project's original implementation):
      - If entry is not a MODEL, score 0.0
      - Presence of model-index results gives base credit
      - Multiple results, tags related to evaluation/benchmarks, cardData model-index,
        and popularity (downloads/likes) increase the score.
      - If nothing found, a small floor score is returned (0.1) to avoid 0 for unknowns.
    """

    def __init__(self):
        super().__init__()

    def calculate_metric(self, data: Dict[str, Any]):
        category = data.get("category", "UNKNOWN")
        if category != "MODEL":
            # Not a model entry -> no performance claims
            self.score = 0.0
            return

        score = 0.0

        model_index = data.get("model_index", [])
        if model_index and isinstance(model_index, list):
            for model_entry in model_index:
                if isinstance(model_entry, dict) and model_entry.get("results"):
                    score += 0.5
                    if len(model_entry["results"]) > 1:
                        score += 0.2
                    break

        tags = data.get("tags", [])
        perf_tags = [
            "arxiv:",
            "leaderboard",
            "benchmark",
            "evaluation",
            "sota",
            "state-of-the-art",
            "performance",
        ]
        if any(
            any(pt in tag.lower() for pt in perf_tags)
            for tag in tags
            if isinstance(tag, str)
        ):
            score += 0.25

        card_data = data.get("cardData", {})
        if (
            isinstance(card_data, dict)
            and card_data.get("model-index", [])
            and not model_index
        ):
            score += 0.3

        downloads = data.get("downloads", 0) or 0
        likes = data.get("likes", 0) or 0
        try:
            downloads = int(downloads)
        except Exception:
            downloads = 0
        try:
            likes = int(likes)
        except Exception:
            likes = 0

        if downloads > 100000 or likes > 500:
            score += 0.4
        elif downloads > 10000 or likes > 100:
            score += 0.3
        elif downloads > 1000 or likes > 10:
            score += 0.2
        elif downloads > 100 or likes > 5:
            score += 0.1

        if score == 0.0:
            score = 0.1

        # Ensure score capped at 1.0
        self.score = min(score, 1.0)
