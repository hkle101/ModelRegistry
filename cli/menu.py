import sys
import json
from typing import Dict, Any
from pathlib import Path
from cli.Metric_tobedeleted.rampup_metric import RampUpMetric
from cli.Metric_tobedeleted.bus_factor_metric import BusFactorMetric
from cli.Metric_tobedeleted.performance_claims_metric import PerformanceClaimsMetric
from cli.Metric_tobedeleted.license_metric import LicenseMetric
from cli.Metric_tobedeleted.size_metric import SizeMetric
from cli.Metric_tobedeleted.dataset_and_code_metric import DatasetAndCodeMetric
from cli.Metric_tobedeleted.dataset_quality_metric import DatasetQualityMetric
from cli.Metric_tobedeleted.code_quality_metric import CodeQualityMetric


METRICS = {
    "1": ("ramp_up_time", RampUpMetric),
    "2": ("bus_factor", BusFactorMetric),
    "3": ("performance_claims", PerformanceClaimsMetric),
    "4": ("license", LicenseMetric),
    "5": ("size_score", SizeMetric),
    "6": ("dataset_and_code_score", DatasetAndCodeMetric),
    "7": ("dataset_quality", DatasetQualityMetric),
    "8": ("code_quality", CodeQualityMetric),
}


WEIGHTS = {
    "ramp_up_time": 0.20,
    "bus_factor": 0.15,
    "performance_claims": 0.15,
    "license": 0.10,
    "size_score": 0.15,
    "dataset_and_code_score": 0.15,
    "code_quality": 0.10,
}


class Menu:
    """Interactive menu wrapper for scoring utilities.

    This class encapsulates the functions previously exposed at module
    level and exposes them as methods so `main.py` can import and
    orchestrate behavior programmatically.
    """

    def __init__(self, urls_file: str = "urls.txt"):
        self.urls_file = urls_file

    def read_urls(self, file_path: str | None = None) -> list[str]:
        p = Path(file_path or self.urls_file)
        if not p.exists():
            print(f"URLs file not found: {p}")
            return []
        return [
            line.strip()
            for line in p.read_text().splitlines()
            if line.strip()
        ]

    def run_score_all(self, urls_file: str | None = None) -> None:
        urls = self.read_urls(urls_file)
        if not urls:
            return
        metrics = [
            RampUpMetric(),
            BusFactorMetric(),
            PerformanceClaimsMetric(),
            LicenseMetric(),
            SizeMetric(),
            DatasetAndCodeMetric(),
            DatasetQualityMetric(),
            CodeQualityMetric(),
        ]

        for u in urls:
            print(f"Scoring: {u}")
            accum: Dict[str, Any] = {}
            for m in metrics:
                try:
                    accum.update(m.timed_calculate(u))
                except Exception as e:
                    print(f"  Metric {m.name} failed: {e}")
            # Compute net_score using same weighting as cli.main
            # size_score may be a dict -> average
            size_obj = accum.get("size_score")
            size_mean = 0.0
            if isinstance(size_obj, dict) and size_obj:
                vals = [float(v) for v in size_obj.values()]
                size_mean = sum(vals) / len(vals)

            net = (
                WEIGHTS["ramp_up_time"] * float(accum.get("ramp_up_time", 0.0))
                + WEIGHTS["bus_factor"] * float(accum.get("bus_factor", 0.0))
                + WEIGHTS["performance_claims"]
                * float(accum.get("performance_claims", 0.0))
                + WEIGHTS["license"] * float(accum.get("license", 0.0))
                + WEIGHTS["size_score"] * float(size_mean)
                + WEIGHTS["dataset_and_code_score"]
                * float(accum.get("dataset_and_code_score", 0.0))
                + WEIGHTS["code_quality"]
                * float(accum.get("code_quality", 0.0))
            )

            net = max(0.0, min(1.0, float(net)))
            net_latency = sum(
                int(v)
                for k, v in accum.items()
                if k.endswith("_latency") and isinstance(v, (int, float))
            )

            accum["net_score"] = net
            accum["net_score_latency"] = int(net_latency)

            print(json.dumps(accum, separators=(",", ":")))
            # Also emit a simple net score line to stderr for visibility
            print(f"net_score: {net}", file=sys.stderr)

    def run_score_metric(
        self, urls_file: str | None, metric_name: str
    ) -> None:
        urls = self.read_urls(urls_file)
        if not urls:
            return
        # find metric by name
        found = None
        for _, (name, cls) in METRICS.items():
            if name == metric_name:
                found = cls()
                break
        if not found:
            print(f"Metric not found: {metric_name}")
            return

        for u in urls:
            try:
                res = found.timed_calculate(u)
                print(f"{u}: {res}")
            except Exception as e:
                print(f"{u}: ERROR {e}")

    def run_tests(self) -> None:
        import subprocess

        subprocess.run([sys.executable, "-m", "pytest", "-q"], check=False)

    def interactive(self) -> None:
        print("Choose an option by typing the number and pressing enter:\n")
        print("1) Score the urls file (urls.txt)")
        print("2) Score the urls file with a specific metric")
        print("3) Run all tests (pytest)\n")

        choice = input("Choice: ").strip()
        if choice == "1":
            self.run_score_all(None)
        elif choice == "2":
            print("Available metrics:")
            for k, (name, _) in METRICS.items():
                print(f"  {k}) {name}")
            m_choice = input(
                "Choose metric by number or name (e.g. 4 or license): "
            ).strip()
            # accept numeric selection or textual name
            sel_name = None
            if m_choice in METRICS:
                sel_name = METRICS[m_choice][0]
            else:
                # allow user to type the metric name directly
                sel_name = m_choice
            self.run_score_metric(None, sel_name)
        elif choice == "3":
            self.run_tests()
        else:
            print("Unknown choice")
