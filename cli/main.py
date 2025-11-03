from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from typing import List

from cli.utils.ModelManager import ModelManager


def read_urls(path: str) -> List[str]:
    """Read URLs from a file, ignoring empty lines."""
    with open(path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines()]
    return [l for l in lines if l]


def ensure_dir(path: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score models from URLs")
    parser.add_argument("--urls-file", default="urls.txt", help="File with one URL per line")
    parser.add_argument("--url", help="Score a single URL (overrides --urls-file)")
    parser.add_argument("--out-dir", default="scored", help="Directory to write JSON results")
    parser.add_argument("--quiet", action="store_true", help="Only print summary paths")
    args = parser.parse_args(argv)

    mgr = ModelManager()
    ensure_dir(args.out_dir)

    urls = [args.url] if args.url else read_urls(args.urls_file)
    results = []

    for u in urls:
        try:
            res = mgr.ScoreModel(u)
        except Exception as e:
            print(f"[ERROR] Scoring failed for {u}: {e}")
            continue

        # Only store Name and Score in the JSON
        json_result = res

        ts = datetime.utcnow().isoformat(timespec="seconds").replace(":", "-")
        out_path = os.path.join(args.out_dir, f"{json_result['Name']}_{ts}.json")

        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(json_result, f, indent=2)
        except Exception as e:
            print(f"[WARN] Failed to write {out_path}: {e}")

        results.append((u, out_path))

        if not args.quiet:
            print(f"\nScored {u} -> {out_path}")
            print(json.dumps(json_result, indent=2))

    # Print a short summary
    print("\nSummary:")
    for u, p in results:
        print(f" - {u} -> {p}")


if __name__ == "__main__":
    main()
