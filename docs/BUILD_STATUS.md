# TenderLens — Current Build Status

**Updated:** 24 October 2026. This file records implementation progress across both frontend and backend tracks.

## Implemented

| Area | Current behavior |
| --- | --- |
| Landing | Product introduction, sample product preview, how-it-works sections, workspace entry points |
| Dashboard | Collapsible sidebar, mobile navigation, persistent shared workspace shell |
| Tender review | Search, category/readiness filters, sort, saved notices, shortlist JSON export |
| Supplier profile | Editable facts, tri-state certificates, exact annual financial periods, optimistic versioning, local browser persistence and backend persistence |
| Backend API & Architecture | FastAPI application factory, PostgreSQL 17/18 persistence in dedicated `tenderlens_api` schema, Alembic async migrations (21 tables), typed Pydantic v2 schemas with camelCase aliases |
| Auth & Isolation | Firebase Auth ID token verification, automatic personal workspace provisioning (`/me`), strict workspace isolation for all profiles, bookmarks, jobs, and private uploads |
| Rules Engine | Authoritative Python domain readiness engine evaluating 5 supported check types (turnover, experience, certificates, deposit, deadline) with reason codes, conservative aggregation, and evidence citations |
| Document Ingestion | PyMuPDF extraction with 1-based page indexing, SHA-256 deduplication, SSRF protections, and clause-quote page verification |
| Amendments & Diff | Snapshot-to-snapshot clause condition comparison classifying added, modified, removed, and unchanged clauses |
| Durable Worker | Background worker utilizing PostgreSQL `FOR UPDATE SKIP LOCKED` row locking, leases, heartbeats, and provider observation budgets |
| TinyFish Provider | Server-only adapter supporting both deterministic `fixture` mode and live `POST /v1/automation/run-async` metered runs with cancellation and reconciliation |
| Local Import | Idempotent `POST /api/v1/imports/local-workspace` migration of browser storage into the persistent backend |
| CLI & Benchmark | `seed.py` for idempotent setup and `benchmark.py` running the 10-notice evaluation target |

## Verification Summary

### Backend
- **Migrations:** Alembic revision applied; all 21 tables created in `tenderlens_api` schema.
- **Test Suite:** 26/26 unit and API integration tests passing in pytest (golden rule boundary conditions, document hashing, downloader SSRF rejection, normalizers, clause extraction, auth/provisioning, profile version concurrency, bookmarks, refresh jobs, local imports).
- **Benchmark:** 10-notice release benchmark completed with 100% extraction (50/50 conditions), 100% page/quote linkage, and 0 silent passes on bad evidence.
- **Code Quality:** Ruff linting and formatting checks passing cleanly across 70 files.

### Frontend
- ESLint and TypeScript checks passed.
- Seventeen behavior tests passed: missing financial years, unknown versus absent certificates, zero funding, evidence requirements, deadline boundaries, incomplete coverage, aggregate status precedence, live result schema checks, no-match semantics, duplicate limits, and source URL restrictions.
- Production build generated landing, dashboard routes, architecture page, sample documents, and dynamic discovery routes.

See [backend/README.md](../backend/README.md) and root [README.md](../README.md) for local setup and commands.
