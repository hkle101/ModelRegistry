# Model Registry & Metrics CLI

This repository contains two main components:

1. Backend API (`backend/`): FastAPI service exposing artifact registration, listing, retrieval, rating, cost estimation, lineage, license checking, regex search, and reset endpoints. All responses include request/response timestamps (headers + `_timestamps` field when JSON dict).
2. Frontend (`frontend/`): Lightweight static HTML pages for interacting with the backend (dashboard, artifact detail view, upload/search page).
3. Metrics CLI (`repo2/` or previously referenced as a metrics runner) that evaluates URLs with a suite of quality metrics and prints one NDJSON record per URL.

Sections below document the metrics CLI (original content preserved) and new frontend usage.

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

---

## Frontend Usage

Directory: `frontend/`

### Pages
- `index.html`: Dashboard exposing all backend endpoints (create, retrieve, update, list, regex search, rate, cost, lineage, license-check, reset, health). Shows timestamps per response.
- `artifact.html`: Focused detail view for a single artifact (metadata, rating, cost, lineage, license check).
- `upload.html`: Artifact creation form plus regex search and listing.

### Shared Scripts
- `scripts/api.js`: Fetch wrapper returning `{ status, data, pretty, requestTs, responseTs }`.
- `scripts/artifacts.js`: Renders artifact arrays as a table.
- `scripts/main.js`: DOM helpers.

### Styling
Global CSS in `assets/style.css` (variables, layout, responsive cards, dark code blocks).

### Running the Frontend
1. Start backend (from repository root):
  ```bash
  uvicorn backend.main:app --reload
  ```
2. Open `frontend/index.html` (or other page) directly in a browser. No build step required.

### Timestamp Metadata
Each backend JSON dict response is augmented with `_timestamps: { request, response }` and headers:
- `x-request-timestamp`
- `x-response-timestamp`

Frontend displays these per result pane.

### Extending
- Add new endpoint panels to `index.html` with `apiCall(method, path, body)`.
- For complex views create a separate HTML file and reuse the scripts.
- Styling utilities (.grid, .card, .timestamps) are available in `style.css`.

---

## Backend Endpoints Summary

| Method | Path                                   | Purpose |
|--------|----------------------------------------|---------|
| POST   | /artifact/{artifact_type}              | Create artifact from URL |
| POST   | /artifacts                             | List artifacts (optional queries) |
| GET    | /artifacts/{artifact_type}/{id}        | Retrieve artifact metadata |
| PUT    | /artifacts/{artifact_type}/{id}        | Update artifact (baseline stub) |
| DELETE | /reset                                 | Reset registry storage |
| POST   | /artifact/byRegEx                      | Regex search by name |
| GET    | /artifact/model/{id}/rate              | Return randomized rating scores |
| GET    | /artifact/{artifact_type}/{id}/cost    | Return randomized cost estimate |
| GET    | /artifact/model/{id}/lineage           | Return mock lineage graph |
| POST   | /artifact/model/{id}/license-check     | Validate GitHub URL reachability |
| GET    | /health                                | Service health check |

Authentication: No authorization required. The previous optional `X-Authorization` header has been removed from the frontend and is not needed by the backend (token dependency currently permissive).

---

## Contributing

1. Keep backend modules free of circular imports—shared singletons live in `backend/deps.py`.
2. Add new routers under `backend/api/` and include them in `backend/main.py`.
3. Extend frontend by adding new sections following existing patterns and using `apiCall`.
4. Ensure new responses preserve timestamp injection (automatic via middleware).

---

## License
Internal / Course Use. Do not redistribute proprietary portions without authorization.


