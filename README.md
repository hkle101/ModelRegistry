# ModelRegistry

FastAPI-based artifact registry (S3 + DynamoDB) with a static HTML frontend.

## What’s in this folder
- `backend/`: FastAPI app (`backend/main.py`) with routers under `backend/api/`
- `frontend/`: static HTML/CSS/JS pages that call the backend
- `cli/`, `metrics/`, `datafetchers/`: scoring + metadata utilities used by the rating flow

## Run locally
From `ModelRegistry/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Alternatively:

```bash
./runlocal.sh
```

Backend base URL: `http://localhost:8000`

## Frontend
No build step. With the backend running, open any of:
- `frontend/index.html`
- `frontend/upload.html`
- `frontend/artifact.html`

The frontend uses `frontend/scripts/api.js` (`API_BASE = 'http://localhost:8000'`).

## Auth
Routers accept an optional `x-authorization` header for compatibility, but `backend/deps.py` currently treats it as a no-op (all requests allowed).

## Timestamps
Every request includes timestamp headers:
- `x-request-timestamp`
- `x-response-timestamp`

If the response body is a JSON object, the backend also injects:

```json
{"_timestamps": {"request": "...", "response": "..."}}
```

## API endpoints
Implemented routers are registered in `backend/main.py`:

- `GET /health` (returns `200`)
- `POST /artifact/{artifact_type}` (create)
	- body: `{ "url": "...", "name": "optional" }`
	- response: `{ metadata: {name,id,type}, data: {url, download_url} }`
- `GET /artifacts/{artifact_type}/{id}` (retrieve)
- `PUT /artifacts/{artifact_type}/{id}` (update placeholder; returns a simple status payload)
- `DELETE /artifacts/{artifact_type}/{id}` (delete)
- `POST /artifacts` (list + pagination)
	- body: array of `{ "name": "...", "types": ["model","dataset","code"]? }`
	- `offset` query param: for pagination
	- response: array of `{name,id,type,url?,download_url?}` and an `offset` response header when more results exist
- `POST /artifact/byRegEx` (regex search)
	- body: `{ "regex": "..." }`
	- searches over stored `name` and `metadata.readme`
- `GET /artifact/model/{id}/rate` (rating)
	- returns cached scores if present; otherwise recomputes via the scoring pipeline
- `GET /artifact/{artifact_type}/{id}/cost` (cost placeholder; currently returns a random `total_cost`)
- `GET /artifact/model/{id}/lineage` (lineage placeholder; returns a minimal graph)
- `POST /artifact/model/{id}/license-check` (license placeholder)
	- body: `{ "github_url": "..." }`
	- validates artifact exists and checks the URL is reachable via `HEAD`
- `DELETE /reset` (clears S3 + DynamoDB)

## AWS configuration
Storage defaults are defined in `aws/config.py`:
- region: `us-east-2`
- bucket: `artifacts-for-modelregistry`
- DynamoDB table: `Artifacts`

Credentials are read from environment variables:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

## Tests
From `ModelRegistry/`:

```bash
pytest -q
```

