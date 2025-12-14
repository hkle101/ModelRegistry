from typing import Any, Dict
from .basemetric import BaseMetric


class RampUpTimeMetric(BaseMetric):
    """
    Class for scoring Ramp Up Time Metric
    """

    def __init__(self):
        super().__init__()

    def calculate_metric(self, data: Dict[str, Any]):
        """Calculate the ramp-up time score based on provided normalized data.

        Expects `data` to be the output of `RampUpTimeDataFetcher`, containing keys
        like: description, cardData, metadata, siblings, tags, widgetData,
        transformersInfo, category.
        """
        # Defensive defaults
        if not data or not isinstance(data, dict):
            self.score = 0.0
            return

        # Helper closures adapted from the old implementation
        def get_description(parsed: Dict[str, Any]) -> str:
            desc = parsed.get("description") or ""
            if not desc:
                meta = parsed.get("metadata") or {}
                desc = meta.get("description") or ""

            if not desc:
                card = parsed.get("cardData") or {}
                desc = card.get("model_description") or card.get("description") or ""
                if not desc:
                    meta = parsed.get("metadata") or {}
                    card = meta.get("cardData") or {}
                    desc = (
                        card.get("model_description") or card.get("description") or ""
                    )
            return str(desc)

        def has_quick_start_guide(parsed: Dict[str, Any]) -> bool:
            description = get_description(parsed).lower()
            quick_start_indicators = [
                "quick start",
                "getting started",
                "quickstart",
                "installation",
                "usage",
                "example",
                "tutorial",
                "how to use",
            ]
            if any(ind in description for ind in quick_start_indicators):
                return True

            siblings = parsed.get("siblings") or parsed.get("metadata", {}).get(
                "siblings", []
            )
            quick_start_files = [
                "quickstart",
                "getting_started",
                "tutorial",
                "example",
                "demo",
                "usage",
                "install",
            ]
            for s in siblings or []:
                if isinstance(s, dict):
                    filename = str(s.get("rfilename", "") or "").lower()
                    if any(qs in filename for qs in quick_start_files):
                        return True
            return False

        def has_installation_instructions(parsed: Dict[str, Any]) -> bool:
            description = get_description(parsed).lower()
            install_indicators = [
                "pip install",
                "conda install",
                "npm install",
                "yarn add",
                "installation",
                "install",
                "setup",
                "requirements",
            ]
            if any(ind in description for ind in install_indicators):
                return True

            tags = parsed.get("tags") or parsed.get("metadata", {}).get("tags", [])
            if isinstance(tags, list):
                for t in tags:
                    if isinstance(t, str) and "transformers" in t.lower():
                        return True

            siblings = parsed.get("siblings") or parsed.get("metadata", {}).get(
                "siblings", []
            )
            install_files = [
                "requirements.txt",
                "package.json",
                "setup.py",
                "pyproject.toml",
                "environment.yml",
                "dockerfile",
                "makefile",
            ]
            for s in siblings or []:
                if isinstance(s, dict):
                    filename = str(s.get("rfilename", "") or "").lower()
                    if any(inst in filename for inst in install_files):
                        return True
            return False

        def has_runnable_examples(parsed: Dict[str, Any]) -> bool:
            widget_data = parsed.get("widgetData") or parsed.get("metadata", {}).get(
                "widgetData", []
            )
            if widget_data:
                return True

            transformers_info = parsed.get("transformersInfo") or parsed.get(
                "metadata", {}
            ).get("transformersInfo", {})
            if isinstance(transformers_info, dict) and transformers_info.get(
                "auto_model"
            ):
                return True

            siblings = parsed.get("siblings") or parsed.get("metadata", {}).get(
                "siblings", []
            )
            example_files = [".py", ".ipynb", "example", "demo", "sample"]
            for s in siblings or []:
                if isinstance(s, dict):
                    filename = str(s.get("rfilename", "") or "").lower()
                    if any(ex in filename for ex in example_files):
                        return True
            return False

        def has_minimal_dependencies(parsed: Dict[str, Any]) -> bool:
            tags = parsed.get("tags") or parsed.get("metadata", {}).get("tags", [])
            lightweight_indicators = [
                "transformers",
                "diffusers",
                "sentence-transformers",
                "sklearn",
                "numpy",
                "pytorch",
                "tensorflow",
            ]
            if isinstance(tags, list):
                framework_count = 0
                for tag in tags:
                    if not isinstance(tag, str):
                        continue
                    for lib in lightweight_indicators:
                        if lib in tag.lower():
                            framework_count += 1
                            break
                if framework_count > 0:
                    return True

            description = get_description(data).lower()
            standalone_indicators = [
                "no dependencies",
                "standalone",
                "zero dependencies",
                "minimal setup",
                "plug and play",
            ]
            if any(ind in description for ind in standalone_indicators):
                return True
            return False

        def get_model_complexity(parsed: Dict[str, Any]) -> str:
            tags = parsed.get("tags") or parsed.get("metadata", {}).get("tags", [])
            size_indicators = {
                "large": ["large", "xl", "big", "giant"],
                "medium": ["medium", "base", "standard"],
                "small": ["small", "mini", "tiny", "micro", "nano"],
            }
            if isinstance(tags, list):
                for size, indicators in size_indicators.items():
                    for tag in tags:
                        if isinstance(tag, str) and any(
                            ind in tag.lower() for ind in indicators
                        ):
                            return size

            description = get_description(parsed).lower()
            if any(
                word in description for word in ["billion", "parameters", "large-scale"]
            ):
                return "large"
            if any(
                word in description for word in ["lightweight", "efficient", "fast"]
            ):
                return "small"
            return "medium"

        def has_clear_documentation(parsed: Dict[str, Any]) -> bool:
            description = get_description(parsed)
            tags = parsed.get("tags") or parsed.get("metadata", {}).get("tags", [])
            known_architectures = [
                "bert",
                "distilbert",
                "gpt",
                "whisper",
                "roberta",
                "t5",
            ]
            is_known_arch = False
            if isinstance(tags, list):
                is_known_arch = False
                for t in tags:
                    if not isinstance(t, str):
                        continue
                    low = t.lower()
                    for arch in known_architectures:
                        if arch in low:
                            is_known_arch = True
                            break
                    if is_known_arch:
                        break
            min_length = 50 if is_known_arch else 100

            if not description or len(description.strip()) < min_length:
                siblings = parsed.get("siblings") or parsed.get("metadata", {}).get(
                    "siblings", []
                )
                doc_files = [
                    "README.md",
                    "README.txt",
                    "README.rst",
                    "docs/",
                    "documentation",
                ]
                for s in siblings or []:
                    if isinstance(s, dict):
                        filename = str(s.get("rfilename", "") or "").lower()
                        if any(doc_file.lower() in filename for doc_file in doc_files):
                            return True
                return False
            return True

        # Begin scoring
        score = 0.0

        desc_text = get_description(data)
        desc_len = len(desc_text or "")

        clear_docs = has_clear_documentation(data)
        if clear_docs:
            # More generous documentation contribution: even shorter docs give
            # a meaningful boost, and long docs can almost carry the metric.
            if desc_len > 300:
                score += 0.40
            elif desc_len > 150:
                score += 0.35
            elif desc_len > 100:
                score += 0.25
            else:
                score += 0.20

        # Quick-start style guidance is very helpful for ramp-up, so weight it
        # more heavily.
        if has_quick_start_guide(data):
            score += 0.30

        # Clear installation instructions are also heavily rewarded.
        if has_installation_instructions(data):
            score += 0.25

        # Runnable examples give a big leg up for ramp-up time.
        if has_runnable_examples(data):
            score += 0.25

        # Minimal dependencies are a nice bonus but not mandatory.
        if has_minimal_dependencies(data):
            score += 0.15

        complexity = get_model_complexity(data)
        if complexity == "small":
            # Small/lightweight models are easier to ramp up on.
            score += 0.10
        elif complexity == "large":
            # Large models are slightly harder to ramp up on, but keep
            # the penalty very small so they are not overly punished.
            score -= 0.02

        category = (data.get("category") or "").upper()
        if category == "DATASET":
            # Datasets tend to be easier to understand once documented.
            score += 0.10
        elif category == "CODE":
            if not has_runnable_examples(data):
                # Lack of runnable examples hurts ramp-up, but only mildly.
                score -= 0.02

        # Be more generous overall: if we found any positive signal and the
        # score is still low, lift it to a moderate floor so partially
        # documented resources do not get overly harsh ramp-up scores.
        if score > 0.0 and score < 0.3:
            score = 0.3

        # clamp to [0,1]
        self.score = max(0.0, min(score, 1.0))
