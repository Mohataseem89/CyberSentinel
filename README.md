# CyberSentinel

CyberSentinel is a full-stack phishing URL risk checker. It combines a calibrated lexical URL model with optional reputation evidence and intentionally avoids opening submitted webpages on the backend.

> CyberSentinel produces risk indicators, not guarantees that a URL is safe. Do not use a result as the sole basis for payments, credential entry, access-control changes, or other high-impact security decisions.

## What is implemented

- URL-only phishing risk analysis with a fixed lexical feature schema.
- Calibrated Random Forest model with a versioned manifest and evaluation report.
- Optional VirusTotal reputation evidence.
- Conservative `Safe`, `Suspicious`, `Dangerous`, and `Unknown` verdicts.
- URL normalization and validation before analysis.
- Remote page-content fetching disabled to reduce SSRF exposure.
- QR-code URL extraction and scanning.
- JWT authentication and role-aware administrative feedback review.
- Owner-scoped scan history APIs with explicit retention opt-in.
- Public Learn, Privacy, and Limitations pages.
- Route-level SEO metadata, canonical URLs, structured data, robots policy, and sitemap.
- CI for linting, unit tests, frontend build, bundle-budget checks, and backend tests.

Legacy global analytics endpoints remain disabled because their previous queries were not owner-scoped.

## Repository layout

```text
backend/                 Flask API, model runtime, database code, tests
  data/                  Runtime model artifacts and generated model card
  ml/                    Dataset governance and offline training pipeline
  routes/                Authentication and owner-scoped history APIs
  services/              URL validation, ML, reputation, risk aggregation
  tests/                 Backend unit/security tests
src/                     React frontend
  components/            UI, auth, feature components, SEO helper
  pages/                 Scanner + public content pages
public/                  robots.txt, sitemap.xml, favicon/social assets
docs/                    Architecture, security, operations, API docs
scripts/                 Build/performance checks
e2e/                     Playwright tests
```

## Quick start

### Prerequisites

- Node.js 22+
- Python 3.12 recommended
- PostgreSQL
- A database/user you can use locally

### 1. Clone

```bash
git clone https://github.com/Mohataseem89/CyberSentinel.git
cd CyberSentinel
```

### 2. Frontend environment

```bash
cp .env.example .env
```

For Windows PowerShell, copy the file manually or use:

```powershell
Copy-Item .env.example .env
```

Set `VITE_API_BASE_URL` to your backend URL. Set `VITE_PUBLIC_SITE_URL` to the public frontend origin in production so canonical and social metadata use the right host.

### 3. Backend environment

```bash
cp backend/.env.example backend/.env
```

Generate unique random values for `SECRET_KEY` and `JWT_SECRET_KEY`. Never reuse examples or commit the real `.env` file.

Required backend variables:

```env
SECRET_KEY=<random-secret>
JWT_SECRET_KEY=<different-random-secret>
DB_USER=<database-user>
DB_PASSWORD=<database-password>
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cybersentinel
FRONTEND_URL=http://localhost:5173
MAX_REQUEST_BYTES=32768
API_RATE_LIMIT_PER_MINUTE=30
```

Optional:

```env
VIRUSTOTAL_API_KEY=
VT_CACHE_TTL_SECONDS=900
VT_CACHE_MAX_ENTRIES=1000
```

### 4. Backend dependencies and database

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment, then:

```bash
pip install -r requirements.txt
python models.py
python app.py
```

Backend: `http://localhost:5000`

### 5. Frontend

From the repository root:

```bash
npm ci
npm run dev
```

Frontend: `http://localhost:5173`

## Model artifacts

The runtime expects the generated files under `backend/data/`:

- `phishing_model.pkl`
- `feature_columns.pkl`
- `probability_calibrator.pkl`
- `model_manifest.json`
- `model_evaluation.json`
- `MODEL_CARD.md`

To prepare a governed dataset and train a new version offline:

```bash
cd backend
python -m ml.prepare_governed_dataset
python -m ml.train_model
```

Do not train from API requests or automatically ingest approved feedback into production models. Review dataset provenance, conflicts, splits, evaluation, calibration, and the generated model card before promotion.

## Data handling summary

Anonymous scans are processed for the response and are not written into scan history by default. Authenticated history retention requires the request header `X-Retain-Scan: true`. When a scan is retained, the current history model stores a SHA-256 hash of the raw URL plus a redacted domain representation rather than the raw URL.

Feedback is different: submitted URL reports store the reported URL and review fields because the report itself is intended for human review. See [`docs/DATA_HANDLING.md`](docs/DATA_HANDLING.md) and the public `/privacy` page before production deployment.

## Search indexing policy

Indexable public routes:

- `/`
- `/learn`
- `/limitations`
- `/privacy`

Private, transactional, result, authentication, dashboard, reporting, QR, history, and admin surfaces are marked `noindex` in the application and are disallowed in `public/robots.txt`. Do not add scan results or user history to the sitemap.

Before production, generate the sitemap with the final absolute HTTPS origin: `PUBLIC_SITE_URL=https://your-domain.example npm run seo:sitemap`. Search Console expects canonical absolute URLs.

## Verification

Frontend:

```bash
npm run lint
npm run test
npm run build
npm run perf:build
npm run test:e2e
```

Backend:

```bash
PYTHONPATH=backend python -m unittest discover -s backend/tests -v
```

For production SEO/accessibility checks, run Lighthouse against `/`, `/learn`, `/limitations`, and `/privacy`, then verify that `/login`, `/dashboard`, `/history`, `/results/*`, `/reporturl`, `/qrcode`, and `/admin/*` expose a `noindex` robots meta directive.

## API documentation

See [`docs/API.md`](docs/API.md). The runtime currently exposes the scanner, authentication, owner-scoped history, feedback review, QR scanning, health, and disabled-retraining controls described there.

## Operations and security docs

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/DATA_HANDLING.md`](docs/DATA_HANDLING.md)
- [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md)
- [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md)
- [`docs/API.md`](docs/API.md)
- [`docs/SECURITY.md`](docs/SECURITY.md)
- [`docs/runbooks/INCIDENT_RESPONSE.md`](docs/runbooks/INCIDENT_RESPONSE.md)
- [`docs/runbooks/KEY_ROTATION.md`](docs/runbooks/KEY_ROTATION.md)
- [`docs/runbooks/DEPLOYMENT.md`](docs/runbooks/DEPLOYMENT.md)
- [`docs/LEGAL_DISCLAIMER.md`](docs/LEGAL_DISCLAIMER.md)

## Chrome extension

The repository includes a prototype extension. Load `extension/` as an unpacked extension only for development/testing. Do not market it as real-time protection unless its blocking/detection behavior has been independently validated.

## Security notes

- Never commit secrets, production database URLs, API keys, or private datasets.
- The in-memory rate limiter is appropriate only for a single process; use a shared store such as Redis for horizontally scaled production deployments.
- Keep the backend CORS origin restricted to the real frontend origin.
- Rotate credentials immediately after suspected disclosure; see the key-rotation runbook.
- Keep public privacy/security statements aligned with the deployed infrastructure, logging, backups, and third-party services.

## Authors

- Mohataseem Khan — [GitHub](https://github.com/Mohataseem89) · [LinkedIn](https://www.linkedin.com/in/mohataseem-khan/)
- Rehan Khan — [GitHub](https://github.com/RehanKhan1704) · [LinkedIn](https://www.linkedin.com/in/rehan-khan-5460b6352/)
- Saad Shaikh — [GitHub](https://github.com/SS07158) · [LinkedIn](https://www.linkedin.com/in/saad-shaikh-1b9265259/)
- Ansari Husain — [GitHub](https://github.com/71-husain) · [LinkedIn](https://www.linkedin.com/in/husain-ansari-7530572bb/)
