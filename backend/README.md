# TenderLens Backend

TenderLens backend API and durable processing worker built with FastAPI, PostgreSQL 17/18 (`tenderlens_api` schema), SQLAlchemy 2 (asyncio), Alembic, PyMuPDF, and TinyFish integration.

## Architecture Highlights

- **Identity & Workspace Isolation:** Firebase Authentication ID token verification with workspace scoping; User A cannot access User B's profiles, bookmarks, jobs, or evidence.
- **Dedicated Database Schema:** Fully managed in PostgreSQL schema `tenderlens_api` with Alembic migrations (`alembic upgrade head`), keeping external schemas isolated.
- **Authoritative Readiness Engine:** 5 deterministic condition groups (Turnover, Experience, Certificates, Deposit/EMD, Deadline) evaluated conservatively with reason codes and evidence citations.
- **Durable Worker & Provider Integration:** Non-blocking background worker with row-level locking (`SELECT ... FOR UPDATE SKIP LOCKED`), leases, heartbeats, and provider observation budgets. TinyFish client operates in both `fixture` (development/testing) and `live` (metered API) modes.
- **Verifiable Document Evidence:** PyMuPDF extraction, SHA-256 content deduplication, SSRF protection against private IP ranges, physical 1-indexed page text, and clause-quote verification.
- **Amendment History:** Condition-level before/after diffs between snapshots.

## Quick Start

### 1. Environment and Dependencies

Ensure Python 3.13 and `uv` are installed. From the `backend/` directory:

```bash
uv sync --python 3.13
cp .env.example .env
```

### 2. Database Migrations

Apply Alembic migrations to create the `tenderlens_api` schema and all 21 tables:

```bash
uv run alembic upgrade head
```

### 3. Register Official Sources

Idempotently register the official sources (e.g. IIIT-Delhi). This command creates no synthetic notices:

```bash
uv run python -m app.cli.seed
```

The provider defaults to `TINYFISH_MODE=live`. Start an authenticated refresh to collect real notices. `fixture` is an explicit testing option, and fixture observations are labelled as samples. Discovery records preserve source titles, dates, and document links; prices and eligibility conditions remain unresolved until source evidence is processed.

### 4. Run the API Server

```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API Docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/healthz`
- Readiness: `http://127.0.0.1:8000/readyz`

### 5. Run the Background Worker

In a separate terminal:

```bash
uv run python -m app.worker
```

## Testing & Quality

### Run Test Suite

Run the full pytest suite (26 unit and API integration tests):

```bash
uv run pytest -v
```

### Run 10-Notice Release Benchmark

Verify extraction accuracy (>=90%), citation coverage (100%), and zero false-pass safety against bad evidence:

```bash
uv run python -m app.cli.benchmark
```

### Code Formatting and Linting

```bash
uv run ruff check .
uv run ruff format --check .
```

## API Routes Overview (`/api/v1`)

| Method & Route | Description |
| --- | --- |
| `GET /healthz`, `GET /readyz` | Liveness and database/storage readiness probes |
| `PUT /api/v1/me`, `GET /api/v1/me` | Provision and retrieve authenticated user and workspace |
| `GET /api/v1/profile`, `PUT /api/v1/profile` | Read and version-update supplier profile with optimistic lock |
| `GET /api/v1/bookmarks` | List bookmarked tenders |
| `PUT /api/v1/bookmarks/{tender_id}` | Save tender to bookmarks |
| `DELETE /api/v1/bookmarks/{tender_id}` | Remove saved tender from bookmarks |
| `GET /api/v1/sources` | Public procurement portal configurations |
| `POST /api/v1/refreshes` | Trigger discovery/refresh job (`202 Accepted`) |
| `GET /api/v1/refreshes/{job_id}` | Check job status and provider progress |
| `POST /api/v1/refreshes/{job_id}/cancel` | Request cancellation of an active job |
| `GET /api/v1/tenders` | Search and filter tenders with live readiness evaluation |
| `GET /api/v1/tenders/{tender_id}` | Detailed tender view with snapshots and findings |
| `GET /api/v1/tenders/{tender_id}/conditions` | Extracted conditions and evidence quotes |
| `GET /api/v1/tenders/{tender_id}/amendments` | Amendment history and clause diffs |
| `POST /api/v1/tenders/{tender_id}/documents` | Bounded manual PDF document upload |
| `GET /api/v1/document-versions/{id}/evidence` | Authorized evidence stream with page citations |
| `POST /api/v1/imports/local-workspace` | Idempotent one-time import of browser local storage |
