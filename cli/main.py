import sys
import json
from typing import Dict, Any
from cli.menu import Menu
from cli.Metric_tobedeleted.license_metric import LicenseMetric
from cli.Metric_tobedeleted.size_metric import SizeMetric
from cli.Metric_tobedeleted.bus_factor_metric import BusFactorMetric
from cli.Metric_tobedeleted.performance_claims_metric import PerformanceClaimsMetric
from cli.Metric_tobedeleted.rampup_metric import RampUpMetric
from cli.Metric_tobedeleted.dataset_and_code_metric import DatasetAndCodeMetric
from cli.Metric_tobedeleted.dataset_quality_metric import DatasetQualityMetric
from cli.Metric_tobedeleted.code_quality_metric import CodeQualityMetric


WEIGHTS = {
    "ramp_up_time": 0.20,
    "bus_factor": 0.15,
    "performance_claims": 0.15,
    "license": 0.10,
    "size_score": 0.15,
    "dataset_and_code_score": 0.15,
    "code_quality": 0.10,
}


def process_url(url: str):
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

    metrics_results: Dict[str, Any] = {}
    for metric in metrics:
        metrics_results.update(metric.timed_calculate(url))

    # Compute net_score as weighted sum
    # size_score is an object; average its values for aggregation
    size_obj = metrics_results.get("size_score", None)
    size_mean = 0.0
    if isinstance(size_obj, dict) and size_obj:
        vals = [float(v) for v in size_obj.values()]
        size_mean = sum(vals) / len(vals)

    net = (
        WEIGHTS["ramp_up_time"]
        * float(metrics_results.get("ramp_up_time", 0.0))
        + WEIGHTS["bus_factor"] * float(metrics_results.get("bus_factor", 0.0))
        + WEIGHTS["performance_claims"]
        * float(metrics_results.get("performance_claims", 0.0))
        + WEIGHTS["license"] * float(metrics_results.get("license", 0.0))
        + WEIGHTS["size_score"] * float(size_mean)
        + WEIGHTS["dataset_and_code_score"]
        * float(metrics_results.get("dataset_and_code_score", 0.0))
        + WEIGHTS["code_quality"]
        * float(metrics_results.get("code_quality", 0.0))
    )

    net = max(0.0, min(1.0, float(net)))
    # collect net latency as sum of metric latencies
    net_latency = sum(
        int(v)
        for k, v in metrics_results.items()
        if k.endswith("_latency") and isinstance(v, (int, float))
    )

    results = metrics_results
    results["net_score"] = net
    results["net_score_latency"] = int(net_latency)

    # Extracts name from URL, handling various formats
    path_parts = url.split("/")
    results["name"] = (
        path_parts[-1]
        if path_parts[-1] and path_parts[-1] != ""
        else path_parts[-2]
        if len(path_parts) > 2
        else url
    )

    # Categorize URL type
    if "huggingface.co/datasets" in url:
        results["category"] = "DATASET"
    elif "huggingface.co" in url:
        results["category"] = "MODEL"
    elif "github.com" in url:
        results["category"] = "REPO"
    else:
        results["category"] = "UNKNOWN"

    return results


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint.

    Usage:
      - Interactive menu: no arguments
      - Score a urls file: main.py path/to/urls.txt
      - Score a single URL: main.py --url https://huggingface.co/...
    """
    argv = argv or sys.argv[1:]
    menu = Menu()

    # no args -> interactive only when running from a terminal.
    # When stdin is captured (for example, during pytest), behave like the
    # previous implementation and print usage / exit so tests that call
    # main() programmatically still receive SystemExit.
    if not argv:
        if sys.stdin is not None and sys.stdin.isatty():
            menu.interactive()
            return 0
        # non-interactive environment: print usage and exit with error
        print("Usage: python3 -m cli.main URL_FILE")
        raise SystemExit(1)

    # single URL via --url
    if len(argv) >= 2 and argv[0] == "--url":
        url = argv[1]
        res = process_url(url)
        print(json.dumps(res, separators=(",", ":")))
        # Print a friendly net score summary to stderr so CLI users see it
        net = res.get("net_score")
        if net is not None:
            print(f"net_score: {net}", file=sys.stderr)
        return 0

    # otherwise treat first arg as urls file
    urls_file = argv[0]
    urls = menu.read_urls(urls_file)
    for u in urls:
        result = process_url(u)
        print(json.dumps(result, separators=(",", ":")))
        # Also emit a simple net score line to stderr for visibility
        net = result.get("net_score")
        if net is not None:
            print(f"net_score: {net}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
