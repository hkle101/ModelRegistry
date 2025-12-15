"""Dataset quality metric implementation.

This module defines DatasetQualityMetric, which scores how well a
dataset is documented and supported with examples, using either a
heuristic or optional GenAI-based evaluation.
"""

import os
import time
import requests
import logging
from typing import Any, Dict
from .basemetric import BaseMetric
try:
    from ModelRegistry.datafetchers.datasetdata_fetcher import DatasetDataFetcher
except ModuleNotFoundError:
    from datafetchers.datasetdata_fetcher import DatasetDataFetcher


class DatasetQualityMetric(BaseMetric):
    """
    Scores dataset documentation and example code clarity.

    Uses an optional GenAI Studio (Purdue) API if configured via
    GEN_AI_STUDIO_API_KEY; otherwise falls back to a deterministic
    heuristic.
    """

    def __init__(self):
        super().__init__()
        self.datafetcher = DatasetDataFetcher()

    def calculate_metric(self, data: Dict[str, Any]):
        # Normalize input using the datafetcher if caller passed raw parsed
        # metadata. Many callers call the datafetcher separately; calling it
        # here is harmless and ensures expected keys exist.
        try:
            parsed = (
                self.datafetcher.fetch_HFdata(data) if isinstance(data, dict) else {}
            )
        except Exception:
            parsed = data or {}

        # If the user provided already-extracted fields, prefer them
        dataset_url = parsed.get("dataset_url") or data.get("dataset_url", "")
        code_url = parsed.get("code_url") or data.get("code_url", "")
        description = parsed.get("description") or data.get("description", "")
        siblings = parsed.get("siblings") or data.get("siblings") or []
        tags = parsed.get("tags") or data.get("tags") or []
        card = parsed.get("cardData") or data.get("cardData") or {}
        downloads = parsed.get("downloads") or data.get("downloads") or 0
        likes = parsed.get("likes") or data.get("likes") or 0
        # transformersInfo/widgetData may appear at top-level in artifact_data
        trans_info = (
            parsed.get("transformersInfo")
            or parsed.get("transformers_info")
            or data.get("transformersInfo")
            or data.get("transformers_info")
            or (card.get("transformersInfo") if isinstance(card, dict) else None)
        )
        widget_data = (
            parsed.get("widgetData")
            or data.get("widgetData")
            or (card.get("widgetData") if isinstance(card, dict) else None)
        )

        api_key = os.getenv("GEN_AI_STUDIO_API_KEY")
        start = time.time()

        # Try the LLM-based route first when API key is present
        if api_key:
            try:
                logging.info("Calling GenAI Studio API for DatasetQualityMetric")
                prompt = f"""
You are a Software Engineer evaluating model resources.
Dataset link: {dataset_url or 'N/A'}
Code link: {code_url or 'N/A'}

Rate the dataset quality from 0.0 to 1.0 based on:
- Dataset documentation clarity
- Presence and usefulness of code examples
- Overall usefulness for developers

Respond with only a number between 0.0 and 1.0.
"""

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }

                payload = {
                    "model": "llama4:latest",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                }

                resp = requests.post(
                    "https://genai.api.purdue.edu/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30,
                )

                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"].strip()
                    score = float(content)
                    self.score = max(0.0, min(1.0, score))
                    self.latency = int((time.time() - start) * 1000)
                    logging.info(f"LLM-based dataset quality score={self.score:.2f}")
                    return
                else:
                    logging.warning(f"GenAI API returned status {resp.status_code}")
            except Exception as e:
                logging.error(f"Error during GenAI API call: {e}", exc_info=True)

        # Fallback to heuristic scoring
        self.score = self._calculate_heuristic_score(
            dataset_url,
            code_url,
            description,
            siblings,
            tags,
            card,
            downloads,
            likes,
            trans_info,
            widget_data,
        )
        self.latency = int((time.time() - start) * 1000)
        logging.info(
            f"Heuristic dataset quality score={self.score:.2f}, latency={self.latency} ms"
        )

    def _calculate_heuristic_score(
        self,
        dataset_url: str,
        code_url: str,
        description: str,
        siblings: Any,
        tags: Any,
        card: Any,
        downloads: int,
        likes: int,
        trans_info: Any,
        widget_data: Any,
    ) -> float:
        score = 0.0

        # Core evidence: dataset and code URLs
        if dataset_url:
            score += 0.3
        if code_url:
            score += 0.3

        # Description length
        desc_len = len(description or "")
        if desc_len > 100:
            score += 0.2
        elif desc_len > 50:
            score += 0.1

        # Documentation files
        has_readme = any(
            isinstance(s, dict)
            and str(s.get("rfilename", "")).upper().startswith("README")
            for s in (siblings or [])
        )
        if has_readme:
            score += 0.1

        # Examples detection: siblings, widgetData, transformersInfo, tags
        has_examples = False
        # filename-based examples
        for s in siblings or []:
            if not isinstance(s, dict):
                continue
            fname = str(s.get("rfilename", "")).lower()
            if any(
                ind in fname for ind in ("example", "demo", "tutorial", ".ipynb", ".py")
            ):
                has_examples = True
                break

        # cardData-based indicators
        try:
            if isinstance(card, dict) and card.get("widgetData"):
                has_examples = True

            # transformersInfo can be inside cardData or at top-level in the parsed data
            trans = trans_info
            if isinstance(trans, dict) and trans.get("auto_model"):
                has_examples = True
            if widget_data:
                has_examples = True
        except Exception:
            pass

        # tags and top-level fields indicating ML/code guidance
        tag_list = [str(t).lower() for t in (tags or []) if isinstance(t, (str,))]
        ml_indicators = (
            "transformers",
            "pytorch",
            "tensorflow",
            "pipeline_tag",
            "task_categories:",
            "task_ids:",
        )
        if any(any(ind in t for ind in ml_indicators) for t in tag_list):
            has_examples = True

        if has_examples:
            score += 0.15

        # ML-specific integration: strong signal that the page is developer-friendly
        ml_integration = False
        if any(
            ind in t
            for t in tag_list
            for ind in ("transformers", "pytorch", "tensorflow")
        ):
            ml_integration = True

        # TransformersInfo is a very strong signal on HF model pages
        has_transformers_info = False
        # Check transformersInfo both in card and at top-level
        if (
            (isinstance(card, dict) and card.get("transformersInfo"))
            or trans_info
            or (isinstance(card, dict) and card.get("pipeline_tag"))
        ):
            ml_integration = True
            has_transformers_info = True

        if ml_integration:
            score += 0.1

        # Give a stronger boost when Transformers integration is explicit
        if has_transformers_info:
            score += 0.2

        # Engagement bumps (small)
        try:
            downloads = int(downloads or 0)
        except Exception:
            downloads = 0
        try:
            likes = int(likes or 0)
        except Exception:
            likes = 0
        if downloads >= 1000:
            score += 0.03
        if likes >= 100:
            score += 0.02

        logging.debug(
            (
                "Heuristic components: "
                f"dataset_url={bool(dataset_url)}, code_url={bool(code_url)}, desc_len={desc_len}, "
                f"readme={has_readme}, examples={has_examples}, ml_integration={ml_integration}, "
                f"downloads={downloads}, likes={likes}"
            )
        )

        return min(score, 1.0)
