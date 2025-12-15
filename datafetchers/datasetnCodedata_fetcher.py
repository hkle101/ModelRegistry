"""Data fetcher that normalizes dataset and code evidence.

Provides a uniform dict shape consumed by dataset-and-code scoring.
"""

# import logging
from typing import Any, Dict

from .basemetricdata_fetcher import BaseDataFetcher


class DatasetAndCodeDataFetcher(BaseDataFetcher):
    """
    Fetcher that extracts dataset + code related evidence from HF metadata
    (or GitHub repo metadata when used for code).

    Produces a uniform dict with keys similar to the old DatasetAndCodeMetric
    implementation so the metric can compute a score.
    """

    def __init__(self):
        super().__init__()

    def _get_description(self, parsed: Dict[str, Any]) -> str:
        desc = parsed.get("description") or ""
        if not desc:
            meta = parsed.get("metadata", {}) or {}
            desc = meta.get("description", "")
        return desc or ""

    def _get_example_count(self, parsed: Dict[str, Any]) -> int:
        if parsed.get("category") == "DATASET":
            card = parsed.get("cardData", {}) or {}
            ds_info = card.get("dataset_info", {})

            if not ds_info:
                meta = parsed.get("metadata", {}) or {}
                ds_info = meta.get("cardData", {}).get("dataset_info", {})

            # dataset_info can be dict or list
            try:
                if isinstance(ds_info, dict):
                    splits = ds_info.get("splits", []) or []
                    total = sum(
                        int(s.get("num_examples", 0))
                        for s in splits
                        if isinstance(s, dict)
                    )
                    # logging.debug(f"Example count (dict splits) = {total}")
                    return total
                elif isinstance(ds_info, list):
                    total = 0
                    for info in ds_info:
                        if isinstance(info, dict):
                            splits = info.get("splits", []) or []
                            total += sum(
                                int(s.get("num_examples", 0))
                                for s in splits
                                if isinstance(s, dict)
                            )
                    # logging.debug(f"Example count (list splits) = {total}")
                    return total
            except Exception:
                return 0
        return 0

    def _get_licenses(self, parsed: Dict[str, Any]) -> str:
        card = parsed.get("cardData", {}) or {}
        lic = card.get("license")

        if not lic:
            meta = parsed.get("metadata", {}) or {}
            lic = meta.get("cardData", {}).get("license")

        if isinstance(lic, list):
            lic = ", ".join(str(x) for x in lic)

        tags = parsed.get("tags") or parsed.get("metadata", {}).get("tags") or []
        if isinstance(tags, list):
            license_tags = [
                t
                for t in tags
                if isinstance(t, str) and t.lower().startswith("license:")
            ]
            if license_tags:
                tag_vals = ", ".join(t.split(":", 1)[1].strip() for t in license_tags)
                combined = f"{lic}, {tag_vals}" if lic else tag_vals
                # logging.debug(f"License detected: {combined}")
                return combined

        return str(lic or "").strip()

    def _ml_integration(self, parsed: Dict[str, Any]) -> bool:
        tags = parsed.get("tags") or parsed.get("metadata", {}).get("tags") or []
        if not isinstance(tags, list):
            tags = []

        ml_indicators = [
            "transformers",
            "pytorch",
            "tensorflow",
            "tf",
            "jax",
            "task_categories:",
            "task_ids:",
            "pipeline_tag",
        ]
        for tag in tags:
            try:
                t = str(tag).lower()
            except Exception:
                continue
            for ind in ml_indicators:
                if ind in t:
                    # logging.debug("ML integration detected from tags")
                    return True

        if parsed.get("pipeline_tag") or parsed.get("transformersInfo"):
            # logging.debug("ML integration detected from pipeline_tag/transformersInfo")
            return True

        return False

    def _get_engagement(self, parsed: Dict[str, Any]) -> Dict[str, int]:
        downloads = parsed.get("downloads")
        likes = parsed.get("likes")
        spaces = parsed.get("spaces")

        meta = parsed.get("metadata", {}) or {}
        downloads = downloads if downloads is not None else meta.get("downloads", 0)
        likes = likes if likes is not None else meta.get("likes", 0)

        if isinstance(spaces, list):
            spaces_count = len(spaces)
        else:
            spaces_count = 0

        try:
            downloads = int(downloads)
        except Exception:
            downloads = 0
        try:
            likes = int(likes)
        except Exception:
            likes = 0

        return {"downloads": downloads, "likes": likes, "spaces": spaces_count}

    def _has_documentation(self, parsed: Dict[str, Any]) -> bool:
        desc = self._get_description(parsed)
        if not desc or len(desc.strip()) < 50:
            return False

        siblings = (
            parsed.get("siblings") or parsed.get("metadata", {}).get("siblings") or []
        )
        doc_files = ["README.md", "README.txt", "README.rst"]
        for s in siblings:
            if isinstance(s, dict):
                fname = str(s.get("rfilename", "")).upper()
                for d in doc_files:
                    if d.upper() in fname:
                        # logging.debug("Documentation file detected")
                        return True

        # If description is long enough and no explicit docs found, assume ok
        return True

    def _has_code_examples(self, parsed: Dict[str, Any]) -> bool:
        widget = (
            parsed.get("widgetData")
            or parsed.get("metadata", {}).get("widgetData")
            or []
        )
        if widget:
            return True

        transformers_info = (
            parsed.get("transformersInfo")
            or parsed.get("metadata", {}).get("transformersInfo")
            or {}
        )
        if isinstance(transformers_info, dict) and transformers_info.get("auto_model"):
            # logging.debug("Code example detected from transformersInfo")
            return True

        example_indicators = ["example", "demo", "tutorial", ".py", ".ipynb"]
        siblings = (
            parsed.get("siblings") or parsed.get("metadata", {}).get("siblings") or []
        )
        for s in siblings:
            if isinstance(s, dict):
                fname = str(s.get("rfilename", "")).lower()
                if any(ind in fname for ind in example_indicators):
                    # logging.debug(f"Code example detected from filename: {fname}")
                    return True

        return False

    def fetch_HFdata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract dataset+code evidence from HF-style metadata dict."""
        self.metadata = {}
        if not isinstance(data, dict):
            return self.metadata

        category = data.get("category") or data.get("type") or "UNKNOWN"

        description = self._get_description(data)
        example_count = self._get_example_count(data)
        licenses = self._get_licenses(data)
        ml_integ = self._ml_integration(data)
        engagement = self._get_engagement(data)
        has_doc = self._has_documentation(data)
        has_examples = self._has_code_examples(data)
        tags = data.get("tags") or data.get("metadata", {}).get("tags") or []
        card_data = (
            data.get("cardData") or data.get("metadata", {}).get("cardData") or {}
        )
        downloads = engagement.get("downloads", 0)
        likes = engagement.get("likes", 0)

        self.metadata.update(
            {
                "category": category,
                "description": description,
                "example_count": example_count,
                "licenses": licenses,
                "ml_integration": ml_integ,
                "engagement": engagement,
                "has_documentation": has_doc,
                "has_code_examples": has_examples,
                "tags": tags,
                "cardData": card_data,
                "downloads": downloads,
                "likes": likes,
            }
        )

        # logging.info(
        #    f"DatasetAndCodeDataFetcher collected data for category={category}"
        # )
        return self.metadata

    # Keep BaseDataFetcher contract: implement Model/Dataset/Code variants
    def fetch_Modeldata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.fetch_HFdata(data)

    def fetch_Datasetdata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.fetch_HFdata(data)

    def fetch_Codedata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # For code (GitHub metadata) try to adapt fields where possible
        # Best-effort: map README/siblings to description and repo/trees to code examples
        return self.fetch_HFdata(data)
