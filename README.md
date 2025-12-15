# ModelRegistry

A FastAPI-based artifact registry backed by S3 + DynamoDB, with a lightweight static HTML frontend and a scoring pipeline (CLI + metrics + data fetchers).

## Contents
- `backend/`: FastAPI app in `backend/main.py` with routers in `backend/api/`
- `frontend/`: static HTML/CSS/JS pages that call the backend (no build step)
- `cli/`: URL ingestion + scoring orchestration utilities
- `metrics/`: metric implementations (8 metrics)
- `datafetchers/`: external-data adapters used by metrics
- `tests/`: unit tests + end-to-end API tests (pytest)

## Quickstart (local)
From `ModelRegistry/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Alternative launcher:

```bash
./runlocal.sh
```

Backend base URL: `http://localhost:8000`

## Frontend
With the backend running, open any of:
- `frontend/index.html` (dashboard)
- `frontend/upload.html` (create, list, regex search)
- `frontend/artifact.html` (lookup, rate, lineage, license-check)

The frontend calls the backend through `frontend/scripts/api.js` (`API_BASE = 'http://localhost:8000'`).

## Authentication
Endpoints accept an optional `x-authorization` header for compatibility. In the baseline implementation, `backend/deps.py` treats authorization as a no-op (all requests allowed).

## Observability
The backend attaches timestamps to every response:
- Headers: `x-request-timestamp`, `x-response-timestamp`
- For JSON object responses only: injects an `_timestamps` field

Example:

```json
{
  "_timestamps": {"request": "...", "response": "..."}
}
```

## API
Routers are registered in `backend/main.py`.

- `GET /health`
- `POST /artifact/{artifact_type}`
  - Body: `{ "url": "...", "name": "optional" }`
  - Response: `{ "metadata": {"name","id","type"}, "data": {"url","download_url"} }`
- `GET /artifacts/{artifact_type}/{id}`
- `PUT /artifacts/{artifact_type}/{id}` (placeholder acknowledgement)
- `DELETE /artifacts/{artifact_type}/{id}`
- `POST /artifacts` (list + pagination)
  - Body: `[ { "name": "...", "types": ["model","dataset","code"]? } ]`
  - Pagination: optional `offset` query param; returns `offset` response header when more results exist
- `POST /artifact/byRegEx`
  - Body: `{ "regex": "..." }`
  - Matches against stored `name` and `metadata.readme`
- `GET /artifact/model/{id}/rate`
  - Returns stored scores if present; otherwise computes via the scoring pipeline
- `GET /artifact/{artifact_type}/{id}/cost` (placeholder)
- `GET /artifact/model/{id}/lineage` (placeholder)
- `POST /artifact/model/{id}/license-check` (placeholder)
  - Body: `{ "github_url": "..." }`
  - Validates artifact exists and checks GitHub URL reachability via `HEAD`
- `GET /artifact/{artifact_id}/download` (302 redirect)
- `DELETE /reset`

## AWS configuration
Defaults live in `aws/config.py`:
- Region: `us-east-2`
- Bucket: `artifacts-for-modelregistry`
- DynamoDB table: `Artifacts`

Credentials are read from environment variables:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

## Testing
From `ModelRegistry/`:

```bash
pytest -q
```

Notes:
- Unit tests isolate external calls using monkeypatching.
- API end-to-end tests patch backend dependencies to avoid AWS/network.

