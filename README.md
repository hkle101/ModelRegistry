# Repo2 CLI (metrics runner)

This folder contains a small CLI that runs several repository/model/dataset
quality metrics and prints one compact NDJSON record per input URL.

This README explains how to run the tool and the sequential flow it follows
for each URL.

## Quick start

1. From the `phase2/repo2` folder run the CLI on a file of URLs (one URL per line):

```bash
# prints one JSON object per line to stdout
python3 -m cli.main urls.txt
```

See `SETUP.md` for step-by-step local setup and virtualenv instructions (macOS/zsh).

Windows Quick start

From the repo folder on Windows you can either use the included wrappers
or run the module directly with Python.

Command Prompt (cmd.exe):

```cmd
run.bat urls.txt
# or run interactively
run.bat
```

PowerShell:

```powershell
.\run.ps1 urls.txt
# or run interactively
.\run.ps1
```

Direct Python invocation (cross-platform):

```powershell
python -m cli.main urls.txt
```

If you use a virtualenv on Windows, activate it first:

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Command Prompt:

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

2. Each printed line is a compact JSON object with metric scores and latency
   fields. Example keys: `name`, `category`, `net_score`, `ramp_up_time`,
   `ramp_up_time_latency`, `performance_claims`, `performance_claims_latency`, etc.

## Sequential flow for each URL

When the CLI processes a single URL it follows these steps in order:

1. Build the metric list
   - The CLI instantiates the metric classes defined in `cli/metrics/`.
   - Current metrics: RampUp, BusFactor, PerformanceClaims, License, Size,
     DatasetAndCode, DatasetQuality, CodeQuality.

2. Run each metric with timing
   - For each metric the CLI calls the metric's `timed_calculate(url)` method.
   - `timed_calculate` runs the metric's `calculate(url)` and measures runtime
     in milliseconds, adding a `{metric_name}_latency` field to the result.

3. Collect metric outputs
   - Each metric returns a small dict of scores (e.g. `{"license": 1.0}`) and
     the latency field. The CLI merges these into a single result dict.

4. Compute net score
   - `net_score` is a weighted combination of per-metric scores (see
     `cli/main.py` for the `WEIGHTS` mapping). If a metric returns a complex
     object (for example `size_score` contains per-device numbers) it is
     reduced (averaged) before aggregation.
   - `net_score` is clamped to the range [0.0, 1.0].

5. Add metadata
   - The CLI adds `name` (derived from the URL) and `category` (MODEL, DATASET,
     REPO, or UNKNOWN) and `net_score_latency` (sum of metric latencies).

6. Print NDJSON
   - The combined result is printed as compact JSON (no extra whitespace),
     one line per input URL.

## Notes & troubleshooting

- The metrics make HTTP calls to public APIs (Hugging Face, GitHub). To avoid
  rate limits when calling GitHub frequently set a `GITHUB_TOKEN` environment
  variable in your shell.
- The CLI is intentionally small and synchronous for easier testing and
  predictability. If you expect to run many URLs, consider batching or
  parallelizing the calls.
- To run the test that compares repo1 vs repo2 outputs, run pytest from
  `phase2/repo2`:

```bash
python3 -m pytest -q
```

## Where to look in the code

- `cli/main.py` — main orchestration: builds metric list, merges results, and
  prints NDJSON.
- `cli/metrics/base.py` — small MetricCalculator helper; subclass metrics must
  implement `calculate(url)` and can use `timed_calculate(url)` to auto-add
  latency.
- `cli/metrics/*.py` — individual metric implementations. When modifying a
  metric, keep behavior deterministic (avoid randomization) so tests can
  compare output across implementations.

If you'd like, I can also run the integration tests and fix any remaining
issues so the repo is fully runnable in CI-style tests.

