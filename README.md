# ModelRegistry

A production-ready model registry system for managing ML models, datasets, and code artifacts with comprehensive quality metrics, AWS deployment, and REST API + web UI.

---

## Features

### Core Functionality
- **CRUD Operations**: Upload, retrieve, update, delete artifacts (models, datasets, code)
- **Quality Rating**: Multi-metric scoring including code quality, dataset quality, license compliance, bus factor, ramp-up time, size compatibility, and performance claims
- **Download Management**: Full-package or selective downloads (weights, datasets) via presigned S3 URLs
- **Model Ingest**: HuggingFace model import with quality gate (≥0.5 on all non-latency metrics)
- **Search & Discovery**:
  - Paginated enumeration with type filtering
  - Regex search across artifact names and metadata
- **Lineage Tracking**: Model lineage graph from structured metadata
- **Cost Analysis**: Size-based download cost estimation
- **License Compatibility**: Cross-check GitHub license against model license for fine-tuning + inference
- **Reset**: Return registry to clean default state

### Additional Metrics (Phase 2)
- **Reproducibility**: Code runnability score (0 / 0.5 / 1)
- **Reviewedness**: Fraction of code introduced via reviewed pull requests
- **Treescore**: Average parent model scores from lineage

### System Health
- `/health` endpoint with real-time metrics
- Web dashboard showing last-hour activity and logs

---

## Architecture

### Tech Stack
- **Backend**: FastAPI (Python 3.11+)
- **Storage**: AWS S3 (artifacts) + DynamoDB (metadata)
- **Deployment**: AWS EC2
- **Frontend**: Vanilla HTML/CSS/JS with responsive design
- **CI/CD**: GitHub Actions

### Project Structure
\`\`\`
ModelRegistry/
├── backend/
│   ├── main.py              # FastAPI app entrypoint
│   ├── deps.py              # Shared dependencies
│   ├── api/                 # Endpoint routers
│   │   ├── create.py
│   │   ├── list.py
│   │   ├── retrieve.py
│   │   ├── rate.py
│   │   ├── cost.py
│   │   ├── license_check.py
│   │   ├── lineage.py
│   │   ├── update.py
│   │   ├── delete.py
│   │   ├── reset.py
│   │   ├── byregex.py
│   │   └── health.py
│   └── services/
│       ├── storage.py       # StorageManager (S3 + DynamoDB)
│       ├── s3_service.py
│       └── dynamodb_service.py
├── cli/
│   └── utils/
│       ├── ArtifactManager.py
│       ├── MetricScorer.py
│       ├── MetadataFetcher.py
│       └── MetricDataFetcher.py
├── metrics/                 # Quality scoring modules
│   ├── codequality.py
│   ├── datasetquality.py
│   ├── busfactor.py
│   ├── license.py
│   ├── rampuptime.py
│   ├── sizescore.py
│   └── performanceclaims.py
├── datafetchers/            # Data acquisition
├── frontend/                # Web UI
│   ├── index.html
│   ├── artifact.html
│   ├── upload.html
│   ├── assets/
│   └── scripts/
├── tests/                   # Unit, integration, E2E
├── docs/
│   ├── architecture.md
│   └── security_case.md
├── requirements.txt
└── pytest.ini
\`\`\`

---

## Getting Started

### Prerequisites
- Python 3.11+
- AWS account with credentials configured
- Virtual environment recommended

### Installation

1. **Clone the repository**
   \`\`\`bash
   git clone https://github.com/hkle101/ModelRegistry.git
   cd ModelRegistry
   \`\`\`

2. **Create and activate virtual environment**
   \`\`\`bash
   python3 -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # .venv\Scripts\activate   # Windows
   \`\`\`

3. **Install dependencies**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

4. **Configure AWS credentials**
   \`\`\`bash
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   export AWS_DEFAULT_REGION=us-east-2
   \`\`\`

5. **Set S3 bucket name** (in \`aws/config.py\`)
   \`\`\`python
   BUCKET_NAME = "your-bucket-name"
   \`\`\`

### Running Locally

**Backend**
\`\`\`bash
cd ModelRegistry
uvicorn backend.main:app --reload
# or
./runlocal.sh
\`\`\`
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

**Frontend**
\`\`\`bash
cd frontend
python3 -m http.server 8080
\`\`\`
- Web UI: http://127.0.0.1:8080

### Running Tests
\`\`\`bash
pytest --cov=. --cov-report=html
\`\`\`

---

## API Endpoints

### Core Operations

#### Create Artifact
\`\`\`
POST /artifact/{type}
Body: { "url": "https://github.com/user/repo" }
\`\`\`

#### List Artifacts (Paginated)
\`\`\`
POST /artifacts?offset=0
Body: [{ "name": "*", "types": ["model", "dataset"] }]
Headers: offset (in response for next page)
\`\`\`

#### Get Artifact
\`\`\`
GET /artifacts/{type}/{id}
\`\`\`

#### Rate Artifact
\`\`\`
GET /artifact/model/{id}/rate
\`\`\`

#### Search by Regex
\`\`\`
POST /artifact/byRegEx
Body: { "regex": "bert.*" }
\`\`\`

#### Get Cost
\`\`\`
GET /artifact/{type}/{id}/cost
\`\`\`

#### License Check
\`\`\`
HEAD /artifact/{id}/license?github_url=...
\`\`\`

#### Lineage
\`\`\`
GET /artifact/{id}/lineage
\`\`\`

#### Reset Registry
\`\`\`
DELETE /reset
\`\`\`

#### Health Check
\`\`\`
GET /health
\`\`\`

---

## Deployment (AWS)

### EC2 Setup
1. Launch EC2 instance (t2.micro free tier)
2. Install dependencies:
   \`\`\`bash
   sudo apt update && sudo apt install -y python3-pip python3-venv
   \`\`\`
3. Clone repo and configure as above
4. Run backend:
   \`\`\`bash
   nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
   \`\`\`
5. Run frontend:
   \`\`\`bash
   cd frontend
   nohup python3 -m http.server 8080 > ../frontend.log 2>&1 &
   \`\`\`

### Monitoring Logs
\`\`\`bash
tail -f backend.log
tail -f frontend.log
\`\`\`

---

## Quality Metrics

| Metric | Description | Score Range |
|--------|-------------|-------------|
| **Code Quality** | Tests, CI, linting, file diversity | 0.0–1.0 |
| **Dataset Quality** | Documentation clarity, examples | 0.0–1.0 |
| **Bus Factor** | Unique contributors (normalized to 50) | 0.0–1.0 |
| **License** | License compatibility tier | 0.0–1.0 |
| **Ramp-up Time** | Quickstart guide, install instructions | 0.0–1.0 |
| **Size Score** | Hardware compatibility (4 devices) | 0.0–1.0 each |
| **Performance Claims** | Evidence of benchmarks/results | 0.0–1.0 |
| **Reproducibility** | Demo code runnability | 0 / 0.5 / 1 |
| **Reviewedness** | PR review coverage | 0.0–1.0 or -1 |
| **Treescore** | Average parent model scores | 0.0–1.0 |

**Net Score**: Weighted average of all metrics with configurable weights.

---

## Security

- **STRIDE threat model** documented in \`docs/security_case.md\`
- **OWASP Top 10** mitigations applied
- **Input validation** for all endpoints
- **Presigned URLs** for time-limited S3 access
- **No hardcoded secrets** (environment variables)

---

## Testing

- **Unit tests**: \`tests/unit/\`
- **Integration tests**: \`tests/integration/\`
- **E2E tests**: \`tests/e2e/\`
- **Coverage target**: ≥60% line coverage

Run specific test suites:
\`\`\`bash
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v
\`\`\`

---

## CI/CD

GitHub Actions workflows:
- **Lint & Test**: On every PR
- **Coverage Report**: Posted to PR comments
- **Deploy**: On merge to \`main\` (optional manual trigger)

Enable Dependabot and GitHub Copilot Auto-Review in repository settings.

---

## Accessibility

Frontend complies with WCAG 2.1 Level AA:
- Semantic HTML landmarks
- ARIA labels for navigation
- Keyboard navigation support
- Color contrast ≥4.5:1
- Focus indicators

---

## Team

- **Team Size**: 2 members
- **Project Management**: GitHub Projects
- **LLM Integration**: GitHub Copilot for development assistance

---

## License

This project is for academic use (Purdue ECE 30861/46100). See course guidelines for details.

---

## Support

For issues or questions:
- Check existing [GitHub Issues](https://github.com/hkle101/ModelRegistry/issues)
- Review [architecture documentation](docs/architecture.md)
- Consult API spec: \`ece461_fall_2025_openapi_spec.yaml\`

---

## Acknowledgments

Built on Phase 1 baseline metrics system with extensions for registry operations, AWS deployment, and comprehensive quality assurance.
