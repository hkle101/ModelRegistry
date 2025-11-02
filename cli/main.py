"""CLI entrypoint for the model-registry scaffold.

This module provides a minimal, testable CLI that reads URLs from a file
or accepts a single `--url` argument and prints JSON results. It delegates
data fetching and scoring to modules under `cli.utils` and the top-level
`metrics` and `datafetchers` packages.
"""

import sys
import json
from typing import Dict, Any
from cli.menu import Menu
from cli.utils.MetricScorer import MetricScorer



WEIGHTS = {
    "ramp_up_time": 0.20,
    "bus_factor": 0.15,
    "performance_claims": 0.15,
    "license": 0.10,
    "size_score": 0.15,
    "dataset_and_code_score": 0.15,
    "code_quality": 0.10,
}


def process_url(url: str) -> Dict[str, Any]:
    """Process a single URL by fetching data and scoring metrics.

    Returns a dictionary suitable for JSON serialization.
    """
    fetcher = None
    scorer = MetricScorer()

    # MetricScorer expects model data fetched by MetricDataFetcher; the
    # MetricScorer.main() convenience method runs fetcher internally, but here
    # we reuse the same flow for a single URL.
    return scorer._score_url(url)


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
        net = result.get("net_score")
        if net is not None:
            print(f"net_score: {net}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
