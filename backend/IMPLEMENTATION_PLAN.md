# TenderLens — Detailed Backend Implementation Plan

**Status:** Proposed implementation; this document does not create a running backend.  
**Prepared:** 24 October 2026, against the current repository.  
**Target:** A Python API and durable processing worker that turn the existing dashboard into an evidence-backed, persistent application.

Related documents: [PRD](../docs/PRD.md), [target architecture](../docs/ARCHITECTURE.md), [overall implementation plan](../docs/IMPLEMENTATION_PLAN.md), and [current build status](../docs/BUILD_STATUS.md).

## 1. Starting point: what exists and what must move

| Repository evidence | Current behavior | Backend work required |
| --- | --- | --- |
| `backend/.venv/pyvenv.cfg` | A Python 3.14.8 virtual environment exists; no application source, dependency manifest, or migrations exist | Establish a reproducible Python project and runtime |
| `frontend/lib/discovery-server.ts` | TinyFish submission and polling run inside Next.js; jobs are local JSON files and browser visits drive polling | Move orchestration into persistent jobs handled independently of the browser |
| `frontend/app/api/discovery/` | Local-development access or a shared discovery token; signed cookies protect run lookups | Replace application access with verified Firebase identity and workspace authorization |
| `frontend/components/workspace-provider.tsx` | Profile, bookmarks, preferences, and live results are browser-local | Persist business data through backend APIs; keep presentation preferences local |
| `frontend/lib/rules.ts` | Five sample rule types run in TypeScript | Implement authoritative Python evaluation with richer period, applicability, and evidence handling |
| `frontend/lib/demo-data.ts` | Eight synthetic notices, two synthetic changes, and a fixed demo clock | Preserve explicit sample mode; create a separately labelled real-document corpus |
| `frontend/lib/auth-context.tsx` | Firebase sign-in and a best-effort Data Connect user upsert are wired | Verify Firebase ID tokens on the backend and provision the application workspace |
| `dataconnect/schema/schema.gql` | Three declared tables: `User`, `SupplierProfile`, `SavedTender` | Define versioned profiles, tender evidence, jobs, evaluations, ownership, and migration boundaries |
| `.github/workflows/ci.yml` | Frontend quality and production smoke checks already run | Add backend checks, a real PostgreSQL test service, and integration checks |

The Data Connect configuration names service `tenderlens-service`, database `tenderlens`, Cloud SQL instance `tenderlens-pg`, and region `us-central1`. These are **configuration values, not proof that the service or database is deployed or reachable**. Verify remote infrastructure during setup.

## 2. Decisions to implement

### 2.1 Application stack

| Component | Proposed choice | Responsibility |
| --- | --- | --- |
| Python | Pin Python 3.13 for the new service | One tested version across development, CI, and containers; reassess 3.14 after dependency/wheel verification |
| Environment and dependencies | `uv`, `pyproject.toml`, committed `uv.lock` | Reproducible installation and separate development dependencies |
| API | FastAPI, Uvicorn, Pydantic v2, pydantic-settings | Validated HTTP API and OpenAPI contract |
| Identity | Firebase Admin Python SDK | Verify the Firebase ID tokens already produced by the frontend |
| Persistence | PostgreSQL, SQLAlchemy 2 async sessions, asyncpg, Alembic | Application-owned records, transactions, and migrations |
| Durable work | PostgreSQL jobs table plus a separate Python worker | Discovery, downloads, extraction, evaluation, and refresh recovery |
| Provider access | TinyFish Python SDK behind an adapter; narrow `httpx` REST fallback if needed | Server-only submit, observe, reconcile, and cancel operations |
| Documents | PyMuPDF and source-specific clause parsers | Text extraction with physical page references |
| Object storage | Filesystem locally; private S3 adapter for the planned AWS deployment | Immutable original PDFs and processing artifacts |
| Validation | pytest, pytest-asyncio, HTTPX, respx, Ruff, mypy | Domain, API, provider, persistence, and worker checks |

The selected Python version is a proposed baseline, not a statement that the current 3.14 environment is broken. Setup must produce a fresh locked environment for the selected version rather than treating the existing `.venv` as a ready backend.

### 2.2 Firebase and database ownership

**Keep Firebase Authentication. Make FastAPI the authoritative API for supplier profiles, bookmarks, tender reviews, and refresh jobs.** Python accesses PostgreSQL through SQLAlchemy; the implementation does not depend on importing the generated JavaScript Data Connect client into Python. The reviewed Data Connect Admin documentation describes a Node.js server integration; Firebase Auth token verification separately supports Python. [Firebase token verification](https://firebase.google.com/docs/auth/admin/verify-id-tokens), [Data Connect Admin integration](https://firebase.google.com/docs/sql-connect/admin-sdk)

Recommended database arrangement:

1. Develop against a local PostgreSQL 17 container.
2. Put all backend-owned tables and the Alembic version table in a dedicated PostgreSQL schema named `tenderlens_api`.
3. Prefer reusing the configured Cloud SQL instance for the first hosted database **if its existence, access, engine compatibility, and schema permissions are verified**. Keep legacy Data Connect tables outside the backend migration scope.
4. If the finale requires the original all-AWS deployment, select RDS PostgreSQL as the replacement domain database before deployment. Use the same Alembic migrations and import process. Do not operate Cloud SQL and RDS as simultaneous writable stores for the same profiles or tenders.
5. During cutover, replace the frontend's Data Connect user upsert with backend `/me` provisioning. Retire direct Data Connect profile/bookmark writes once those resources move to FastAPI.

If Data Connect and backend tables share a database, explicitly configure Data Connect's PostgreSQL `schemaValidation` as `COMPATIBLE`, inspect migration diffs, and test preservation of backend tables. Its strict migration mode can remove elements absent from its application schema. Alembic must whitelist only `tenderlens_api`; a Firebase deployment must never become an implicit migration of the backend's tables. These are two migration tools with disjoint ownership, not two schema definitions for the same tables. [Firebase migration modes](https://firebase.google.com/docs/sql-connect/manage-schemas-and-connectors), [configuration reference](https://firebase.google.com/docs/sql-connect/configuration-reference)

Before preserving any existing direct connector operation, audit its ownership checks. In particular, `DeleteSavedTender($id)` currently declares authenticated-user access but has no visible owner predicate in its mutation body. Require a cross-user deletion test before allowing that path to remain exposed.

### 2.3 Keep the first deployment small

- One API service and one worker service, built from the same backend image.
- One PostgreSQL domain store and one object store.
- One approved source: IIIT-Delhi; one active TinyFish run by default.
- No Redis/Celery/SQS dependency for the initial worker.
- No OCR, arbitrary portal support, bid submission, or general legal interpretation in this backend phase.

These are implementation choices for the MVP. They do not limit later scaling or source coverage.

## 3. Backend structure and module boundaries

Create the following files during implementation. The only files added by the planning task are this plan and the backend README.

```text
backend/
  IMPLEMENTATION_PLAN.md
  README.md
  pyproject.toml
  uv.lock
  .python-version
  .env.example
  Dockerfile
  .dockerignore
  compose.yml
  alembic.ini
  migrations/
    env.py
    versions/
  app/
    __init__.py
    main.py                    # FastAPI application factory and lifespan
    worker.py                  # Durable job runner entry point
    core/
      config.py                # Typed environment settings
      auth.py                  # Firebase token verification and principal
      authorization.py         # Workspace/resource access dependencies
      errors.py                # Public error codes and exception mapping
      logging.py               # Structured logs and redaction
      clock.py                 # Injectable live and demo clocks
    api/
      dependencies.py          # Per-request sessions and services
      routes/
        health.py
        me.py
        profiles.py
        bookmarks.py
        sources.py
        refreshes.py
        tenders.py
        evidence.py
        amendments.py
        imports.py
    schemas/                   # Pydantic request/response contracts
    models/                    # SQLAlchemy table definitions
    repositories/              # Database access and ownership predicates
    services/
      profiles.py
      bookmarks.py
      discovery.py
      ingestion.py
      evaluation.py
      amendments.py
      imports.py
    integrations/
      tinyfish_client.py
      firebase_identity.py
      storage.py               # Filesystem and S3 implementations
    sources/
      iiitd.py                 # Fixed URLs, goal templates, source rules
      policies.py              # Navigation/download allowlists
    documents/
      downloader.py
      hashing.py
      extract_pages.py
      extract_clauses.py
      normalize_amounts.py
      normalize_periods.py
      normalize_dates.py
    domain/
      conditions.py
      readiness.py
      turnover.py
      experience.py
      certificates.py
      deposit.py
      deadline.py
      document_resolution.py
      condition_diff.py
    jobs/
      states.py
      leases.py
      handlers.py
      retries.py
      reconcile.py
    cli/
      seed.py
      benchmark.py
      reconcile_run.py
      import_legacy.py
  tests/
    unit/
    api/
    integration/
    fixtures/
      tinyfish/
      documents/
      labels/
      golden_rules/
```

Routes validate requests and return schemas. Services coordinate use cases. Repositories own SQL and access predicates. Domain rules take facts and an explicit clock; they do not fetch URLs, read environment variables, or call Firebase/TinyFish. The worker calls the same services as the API where appropriate.

Use one SQLAlchemy `AsyncSession` per request or worker unit of work. Do not share a session between concurrent tasks or hold a database transaction open while waiting for TinyFish or downloading a PDF. [SQLAlchemy async session guidance](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

## 4. Environment and local setup

### 4.1 Dependencies and configuration

Create `pyproject.toml` with application dependencies from section 2, a `dev` dependency group, package discovery for `app`, and Ruff/mypy/pytest settings. Commit the resolved `uv.lock`; verify PyMuPDF and database-driver installation on macOS and the Linux CI/container image. Use a Debian slim Python image initially to avoid unnecessary native-library work.

Proposed `backend/.env.example` values:

```dotenv
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000
DATABASE_URL=postgresql+asyncpg://tenderlens:tenderlens_dev@127.0.0.1:5432/tenderlens
DATABASE_SCHEMA=tenderlens_api
FIREBASE_PROJECT_ID=tenderlens-app-2026
# Set this only for a local Auth Emulator; reject it in production.
FIREBASE_AUTH_EMULATOR_HOST=
# Optional local ADC file path. Hosted workloads should use workload identity.
GOOGLE_APPLICATION_CREDENTIALS=
STORAGE_BACKEND=filesystem
LOCAL_STORAGE_PATH=.data/evidence
AWS_REGION=
S3_BUCKET=
TINYFISH_API_KEY=
TINYFISH_BASE_URL=https://agent.tinyfish.ai
TINYFISH_MODE=fixture
MAX_PROVIDER_CONCURRENCY=1
TINYFISH_MAX_DURATION_SECONDS=300
PROVIDER_OBSERVATION_BUDGET_SECONDS=360
PROVIDER_POLL_INTERVAL_SECONDS=15
SOURCE_CACHE_TTL_SECONDS=600
SOURCE_REFRESH_COOLDOWN_SECONDS=60
MAX_PDF_BYTES=20971520
MAX_PDF_PAGES=150
PDF_PARSE_TIMEOUT_SECONDS=30
JOB_LEASE_SECONDS=90
JOB_HEARTBEAT_SECONDS=20
LOG_LEVEL=INFO
```

The database credentials above are local development placeholders. Use separate migration/runtime roles and managed secrets in hosted environments. Ensure `.env`, object artifacts, credentials, and virtual environments stay ignored. The server must fail startup for a production Auth Emulator setting or a live provider mode with no API key.

`TINYFISH_MODE=fixture` must produce explicitly labelled fixture results; it cannot silently masquerade as live mode. The frontend needs only server-side `BACKEND_API_URL` to reach the new API through its proxy. The TinyFish key must leave the Next.js runtime after cutover.

### 4.2 Intended startup commands

These commands become runnable after the scaffold, lockfile, migrations, Compose service, and CLI entry points have been implemented:

```sh
cd backend
uv sync --python 3.13 --all-groups
cp .env.example .env
docker compose up -d db
uv run alembic upgrade head
uv run python -m app.cli.seed --mode demo
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal, from `backend/`:

```sh
uv run python -m app.worker
```

Configure Compose with a PostgreSQL health check, a named data volume, and a loopback-only development port. Seed commands must be idempotent, must not start paid runs, and must never insert synthetic notices into the live collection namespace. `uv` should manage the chosen interpreter/environment rather than relying on whatever packages happen to be in the current virtual environment. [uv project workflow](https://docs.astral.sh/uv/guides/projects/)

### 4.3 Initial operational endpoints

- `GET /healthz`: process liveness; no external API call.
- `GET /readyz`: bounded database check and required local/storage configuration checks; return `503` when unavailable.
- `GET /openapi.json`: generated application contract.
- `/docs`: enabled locally; configure access/exposure for the hosted service.

Readiness must not start TinyFish, download documents, or require a paid provider call.

## 5. Authentication and workspace isolation

1. The existing Firebase client signs in the user and obtains an ID token using `getIdToken()`.
2. The frontend sends `Authorization: Bearer <id_token>` to a fixed same-origin Next.js backend proxy.
3. The proxy forwards the bearer token to FastAPI. It does not accept a client-selected backend URL or manufacture a trusted user ID header.
4. FastAPI verifies the ID token with Firebase Admin, including its project/issuer, signature, and expiry. Trust the verified Firebase UID, not `uid`, `email`, or `workspace_id` in a request body.
5. `PUT /api/v1/me` idempotently provisions an application user and one personal workspace from verified claims; `GET /api/v1/me` reads the resulting context. The first backend release need not implement organisation invitations or shared roles.
6. Every profile, bookmark, job, evaluation, upload, and evidence lookup is scoped through that workspace membership. Use `404` for inaccessible resource IDs where appropriate.
7. Refresh the frontend ID token once on a token-expiry response; do not create a custom password/token system alongside Firebase.

Use Application Default Credentials or workload identity for hosted Firebase Admin access. For local integration, use the Auth Emulator or a development service-account configuration outside Git. Normal Firebase ID-token verification does not automatically implement all revocation policy; decide and test revocation checks for sensitive mutations rather than assuming a decoded token proves a current session. [Firebase ID-token verification](https://firebase.google.com/docs/auth/admin/verify-id-tokens)

If a future client bypasses the Next.js proxy, configure an exact CORS origin allowlist and allow only required methods/headers. Browser cookies are not the new API's identity boundary. Retire the shared `DISCOVERY_ACCESS_TOKEN` and run-signature-cookie scheme after authenticated backend discovery is established.

**Acceptance:** User A cannot read, edit, cancel, delete, or obtain evidence for User B's private resources, even with a valid UUID or old browser-stored job ID.

## 6. Database and migration plan

### 6.1 Tables and constraints

Build the identity/profile/bookmark subset first; introduce pipeline tables with the worker phases.

| Table | Essential fields and constraints |
| --- | --- |
| `users` | UUID PK, unique `firebase_uid`, identity fields, created/last-seen timestamps |
| `workspaces` / `workspace_memberships` | Workspace ID; user membership; unique workspace/user pair; personal workspace creation is idempotent |
| `supplier_profiles` | Workspace ID, current version pointer; one active logical profile per workspace |
| `supplier_profile_versions` | Profile/version unique pair, immutable validated facts JSONB, facts provenance, creator/time |
| `bookmarks` | Workspace ID, stable tender ID, saved time; unique `(workspace_id, tender_id)` |
| `sources` | Stable source ID, fixed start URL, approved hosts, adapter version, enabled flag |
| `refresh_jobs` | Workspace/source/mode/scope, state, checkpoints, next attempt, lease/fencing token, heartbeat, idempotency key, error code |
| `provider_attempts` | Job ID, attempt number, submission state/correlation marker, unique provider run ID when known, provider status and timings |
| `source_observations` | Job/attempt IDs, observed time, raw provider object key, validated notice payload, provenance, completeness |
| `tenders` | Stable UUID, source, trusted external reference or provisional identity, aliases; identity conflicts remain explicit |
| `documents` | Tender association, logical source URL, role, source publication metadata, visibility, and workspace owner for private uploads; do not identify versions by URL alone |
| `document_versions` | Document ID, SHA-256, immutable blob key, observation metadata; unique document/hash association |
| `parse_artifacts` | Document version, parser version, page/text artifact key, extraction outcome and coverage issues |
| `tender_snapshots` | Selected document versions/artifacts, listing observations, effective-condition fingerprint, amendment resolution state; distinguish public source snapshots from workspace-specific upload overlays |
| `conditions` / `condition_evidence` | Snapshot, stable clause identity, normalized predicate, mandatory/applicability states; one or more exact document/page spans |
| `evaluations` / `findings` | Workspace, profile version, snapshot, rule version, evaluation clock/valid-until, status/reasons, supplier-fact references |
| `amendment_changes` | Old/new snapshot and clause identities, before/after values and evidence, material/document-only classification; dedupe key |
| `audit_events` | Workspace/actor/job/resource IDs, event type, time; no raw tokens or secret values |

Private evaluations must never be served from a cache keyed only by tender ID. Public source/document artifacts can be reused; supplier facts and evaluation outputs remain workspace-scoped.

Manual uploads must carry a non-null workspace owner and private visibility. Their snapshots, conditions, and evidence inherit that scope. An uploaded amendment may affect that workspace's review but must not silently replace the global official-source snapshot for other users. Sharing an underlying content-addressed blob does not share its authorization.

### 6.2 Canonical representations

- Store money as `NUMERIC`/Python `Decimal`, with explicit currency. Serialize canonical API monetary values as decimal strings; use an adapter while migrating the current numeric frontend fields.
- Represent turnover by exact financial year, currency, and amount. Preserve whether a requirement is annual, average, aggregate, or otherwise unsupported.
- Use timezone-aware timestamps, stored in UTC; display in Asia/Kolkata by default. Keep raw source date text and any explicit timezone basis.
- Preserve certificate presence as `present`, `absent`, or `unknown`, plus validity/scope when known. Missing validity is distinct from an expired certificate.
- Preserve the source of supplier facts: self-reported, uploaded, or reviewed. Do not imply documentary verification merely because a checkbox is true.
- Assign internal tender UUIDs independently of TinyFish run IDs. The current `live-<run>-<index>` IDs must not become long-term bookmark identities.
- Keep raw bytes immutable. Parser/rule upgrades create new artifacts/evaluations instead of changing historical evidence in place.

### 6.3 Migration discipline

Alembic must explicitly create/use `tenderlens_api`, place its version table there, and exclude legacy Firebase objects from autogeneration. CI must apply migrations to a blank database and test an upgrade from the preceding schema. Runtime startup checks migration readiness; it does not silently create tables with `create_all()`.

Legacy Data Connect profiles store `turnoverLakhs` plus `turnoverYears`; those fields do not establish exact annual figures or average-versus-aggregate basis. Preserve them as unmapped legacy facts until the supplier confirms the missing details. Do not manufacture three annual values to fill the new model. Import bookmark references, but discard client-submitted readiness as an authoritative evaluation.

## 7. API contract

Use `/api/v1` on FastAPI, camelCase response aliases where they reduce frontend churn, UTC ISO timestamps, UUID identifiers, and a documented error envelope. The Next.js proxy may expose `/api/backend/v1/*`; existing `/api/discovery*` routes can remain temporary compatibility wrappers during migration.

| Method and route | Behavior |
| --- | --- |
| `PUT /me` | Idempotently provision user and personal workspace from verified identity |
| `GET /me` | Read verified user and existing workspace context |
| `GET /profile` | Current facts, immutable version ID, and optimistic concurrency value |
| `PUT /profile` | Validate facts, require `If-Match`/expected version, create a new profile version, enqueue local re-evaluation |
| `POST /imports/local-workspace` | Explicit, idempotent import of the signed-in user's browser profile/bookmarks; return mapping and rejected facts |
| `GET /bookmarks` | Paginated saved tender IDs and current server-derived display state |
| `PUT /bookmarks/{tender_id}` | Idempotently save a known tender for this workspace |
| `DELETE /bookmarks/{tender_id}` | Idempotently remove this workspace's bookmark |
| `GET /sources` | Source configuration safe for clients, freshness, last accepted observation; no credentials |
| `POST /refreshes` | Validate source/mode/watch scope; require `Idempotency-Key`; return `202` with an application job |
| `GET /refreshes/{job_id}` | Persisted application stage, provider status, progress, provenance, and sanitized failures |
| `POST /refreshes/{job_id}/cancel` | Request cancellation; reconcile actual provider outcome before reporting terminal state |
| `GET /tenders` | Cursor pagination plus search, category, readiness, saved, changed, and source filters |
| `GET /tenders/{tender_id}` | Current effective snapshot, coverage, profile-specific evaluation, and unresolved issues |
| `GET /tenders/{tender_id}/conditions` | Normalized requirements and exact source spans |
| `GET /tenders/{tender_id}/evaluations` | Reproducible historical evaluations for this workspace |
| `GET /tenders/{tender_id}/amendments` | Document history and condition-level before/after changes |
| `GET /document-versions/{id}/evidence` | Authorized short-lived file access plus page and provenance metadata |
| `POST /tenders/{tender_id}/documents` | Bounded manual PDF upload with role and explicit manual provenance; no automatic authenticity claim |

An evaluation response must distinguish `status`, `coverageComplete`, `freshness`, `profileVersion`, `snapshotId`, `ruleVersion`, `evaluatedAt`, and `validUntil`. A job response must distinguish collection completion from document/evaluation completion. Preserve the frontend status values `meets`, `review`, and `blocked`; expose provider state separately.

Example accepted refresh response:

```json
{
  "job": {
    "id": "f12b548f-7cc8-475f-9f12-572e3eb98723",
    "status": "queued",
    "stage": "discovery",
    "providerStatus": null,
    "providerRunId": null,
    "cacheHit": false,
    "progress": { "documentsDiscovered": 0, "documentsProcessed": 0 }
  }
}
```

Example public error envelope:

```json
{
  "error": {
    "code": "PROFILE_VERSION_CONFLICT",
    "message": "Your supplier profile changed. Reload it before saving.",
    "requestId": "req_01",
    "retryable": false
  }
}
```

Use `401` for invalid/missing identity, `403` for disallowed actions, `404` for absent/inaccessible resources, `409` for version/idempotency conflicts, `413` for upload limits, `422` for invalid facts, `429` for quotas/cooldowns, and `503` for required unavailable services. Never return raw provider exceptions or internal credential paths.

## 8. Durable jobs and TinyFish integration

### 8.1 Job lifecycle

```text
queued → submitting → discovering → validating → ingesting → extracting
       → evaluating → publishing → completed

Any active stage → retry_wait → resume the same checkpoint
Submission ambiguity → submission_unknown → reconcile → resume or needs_operator
Cancel request → cancel_requested → reconcile provider → cancelled or continue completion
Unrecoverable processing error → failed
```

`provider_status` remains a separate field with TinyFish's `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, or `CANCELLED` value. A provider-completed run can still fail application validation or have documents that need review.

### 8.2 Claiming, deduplication, and recovery

- Claim due jobs in a short transaction using row locks and `FOR UPDATE SKIP LOCKED`; commit before making network calls. PostgreSQL documents this option as suitable for queue-like consumers. [PostgreSQL SELECT locking](https://www.postgresql.org/docs/17/sql-select.html)
- Start with one worker and one provider slot. Enforce the slot in the database, not only a Python process global, so a second API/worker replica cannot bypass it.
- Deduplicate active requests by workspace/source/mode/scope. An idempotency key is bound to the authenticated workspace and request-body hash; reusing it with different parameters returns `409`.
- A fresh reusable public source snapshot can satisfy a request with `cacheHit=true`. Record its original observation time and provider provenance. Do not change its timestamp to imply a new collection.
- Use leases, periodic heartbeats, and a fencing token. An expired worker cannot publish after another worker has reclaimed the job.
- Persist stage outputs and provider run IDs immediately. Restart recovery resumes a known run or parse artifact instead of repeating paid discovery.
- Do not keep the job alive only in FastAPI `BackgroundTasks`. The separate worker must keep progressing after the browser closes or the API process restarts. FastAPI's own guide distinguishes small in-process tasks from larger background processing; the database worker is the application-specific durability choice here. [FastAPI background tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

### 8.3 Provider adapter contract

Implement `submit(goal, schema)`, `get_run(run_id)`, `find_by_correlation(marker)`, and `cancel(run_id)`. Keep the initial request schema aligned with `frontend/lib/tinyfish-schema.ts` and the validated missing-field behavior in `frontend/lib/discovery-validation.ts`.

Verified HTTP contract:

| Operation | TinyFish contract |
| --- | --- |
| Start | `POST https://agent.tinyfish.ai/v1/automation/run-async` |
| Observe | `GET /v1/runs/{run_id}` |
| Reconcile an ambiguous start | List/search existing runs using the application correlation marker |
| Cancel | `POST /v1/runs/{run_id}/cancel`, then inspect the actual returned state |
| Credential | Server-only `X-API-Key` |

Use the official SDK when its pinned version exposes the required lifecycle and retry controls. Disable blind automatic retries of a potentially accepted submission; if those controls are insufficient, use the narrow HTTPX adapter. The browser never talks to TinyFish directly. [TinyFish Agent reference](https://docs.tinyfish.ai/agent-api/reference)

Preserve these collection rules:

1. Fixed source configuration and approved public hosts; do not accept an arbitrary URL from the browser.
2. Up to five relevant notices per bounded discovery run, including every observed associated amendment link.
3. A separate watched-tender refresh revisits saved references even when they disappear from the top-five discovery results.
4. Send category/keyword scope where needed, but no supplier finances, certificates, contact information, or other private profile facts.
5. Keep unknown scalar fields `null`; do not synthesize deadlines, IDs, PDFs, or eligibility.
6. Accept output only after checking provider state, output schema, semantic outcome, duplicate notices, and source URLs. `no_matches` is a valid empty observation, not a reason to delete earlier notices.
7. Keep the provider-facing schema explicit: an object wrapping the notices array, `nullable: true`, and supported keywords. Do not send unadapted Pydantic JSON Schema with unsupported references, type arrays, or extra keywords. [Structured output](https://docs.tinyfish.ai/key-concepts/structured-output)

### 8.4 Retry policy

| Event | Required behavior |
| --- | --- |
| Poll timeout, temporary 5xx | Retry lookup of the same run with bounded backoff |
| 429 | Respect retry guidance within budget; reschedule the job |
| 400/schema failure | Fail with an actionable configuration error; do not retry unchanged input |
| 401/403/billing rejection | Stop automatic attempts; expose an account/configuration reason |
| Start timeout or ambiguous server error | Persist `submission_unknown`; reconcile by correlation marker before any replacement |
| Known provider failure | Allow at most one configured replacement only after confirming the old run is terminal and checking budget |
| Observation budget exceeded | Request cancellation and reconcile; a concurrent completion must still be processed correctly |
| Worker crash after submit | Recover the persisted attempt; if the provider ID was not saved, use correlation-based reconciliation |

Measure the observation budget from the provider attempt's submission time, not the time a job entered a queue. Preserve that deadline across restarts. Initial values are 300 seconds provider execution and 360 seconds observation, with approximately 15-second polling. Document-processing jobs have separate limits.

TinyFish run creation is not assumed to provide exactly-once semantics. Application idempotency, reconciliation, and fencing reduce duplicate work; they cannot justify blindly replaying an uncertain metered submission.

## 9. Document ingestion and exact evidence

### 9.1 Download and storage

1. Validate HTTPS URL, exact approved host, port, and absence of embedded credentials. Review real IIIT-Delhi document hosts before expanding the allowlist.
2. Reject private, loopback, link-local, and mapped private destinations. Revalidate redirects and enforce the approved destination at connection/egress time to address DNS changes.
3. Apply connection/read/total timeouts, a bounded redirect count, streamed byte limits, and PDF signature/type checks.
4. Compute SHA-256 over the original bytes and store the immutable blob. Preserve observations separately from physical-byte deduplication.
5. Re-download watched URLs when needed: the same URL can serve a replacement PDF. HTTP validators are optimizations; content hashes determine actual byte changes.
6. Store originals and raw provider observations privately. Return authorized, short-lived evidence links rather than public bucket access.

Suggested keys: `pdf/{sha256}.pdf`, `provider/{attempt_id}.json`, and `pages/{sha256}/{parser_version}.json`. Keep storage access behind an adapter; credentials or bucket names must not leak into public error messages.

### 9.2 Extraction and clause normalization

- Run PyMuPDF in a bounded child process or isolated worker task; a malformed file must not take down the API or block worker heartbeats.
- Preserve raw text per physical page, a separately normalized form, and optional bounding boxes. Physical page numbers are one-based for the UI; printed page labels are additional metadata.
- Extract clause candidates from headings, paragraphs, nearby text, and source-specific table patterns. Support a clause spanning more than one page with multiple evidence spans.
- Validate that every quoted span occurs on the cited document page before publishing it as evidence.
- Normalize INR amounts, lakh/crore multipliers, exact financial years, comparison operators, dates, and mandatory/applicability language. Preserve the raw text beside normalized values.
- Treat unreadable pages, unsupported table structures, ambiguous periods, exceptions, or conflicting values as unresolved coverage. An extraction exception is not proof that a requirement is absent.
- Record parser version and diagnostics. A changed parser produces a new parse artifact and re-evaluation; it must not rewrite earlier evidence.

Begin with 20 MiB, 150 pages, and a 30-second parse limit, then calibrate against the actual corpus. Scanned PDFs remain Review needed until OCR becomes a separately implemented feature. Manual upload is an explicitly labelled input path, not proof of authenticity or a substitute for OCR.

**Acceptance:** A user can open a real original PDF and the exact page/quote behind a reported condition; every extracted condition has valid evidence references.

## 10. Readiness engine

Port the intent of the current TypeScript rules, but do not reproduce sample-only assumptions as general tender interpretation. The backend is authoritative for live evaluations. Keep the frontend engine only for the explicitly offline sample experience.

| Rule | Initial supported behavior | Must remain unresolved |
| --- | --- | --- |
| Turnover | Explicit annual/average/aggregate threshold for exact known financial years and currency, using Decimal | Missing years, unknown basis, unclear relative period, currency conversion |
| Experience | Explicit count/value/completion-window predicates with known work-category mapping | Unclear “similar work”, unsupported AND/OR alternatives, ambiguous customer or completion restrictions |
| Certificates | Explicit certificate identity, declared presence, and applicable validity/scope checks | Unknown presence, missing required validity, unclear issuer/scope, unresolved exemption |
| Deposit/EMD | Known amount against same-currency declared funding capacity | Unknown percentage base, disputed waiver, guarantees or payment confirmation beyond scope |
| Deadline | Exact, unambiguous timestamp and verified amendment precedence against the server clock | Date-only text, unresolved timezone, contradictory listing/PDF values |

Evaluate each applicable mandatory predicate, including multiple conditions within one group. For every supported group, track extracted conditions, an evidenced non-applicability decision, or an explicit coverage gap. Finding five type labels does not establish that the entire notice was parsed completely.

Aggregate using these rules:

1. A confirmed failure of a current mandatory requirement produces `blocked`; preserve other unresolved findings.
2. Otherwise, an unresolved predicate, unaccounted group, ambiguous amendment, or incomplete relevant document set produces `review`.
3. Only a nonempty, fully accounted set of passing applicable checks can produce `meets`.
4. An old result that could have been superseded remains historical. Do not use a prior blocker or pass as the current result when a new unreadable amendment may have changed it.

Each finding records a reason code, comparison inputs, supplier-fact source, requirement evidence, and any limitation. Display “Meets checked conditions”; do not claim universal eligibility or that an EMD has been paid.

An evaluation is identified by workspace, profile version, effective tender snapshot, parser/rule versions, and clock. Set `validUntil` to the next relevant deadline/certificate/time boundary. The worker schedules re-evaluation then; API reads must not return an expired cached pass as current. Profile edits enqueue local re-evaluation without another TinyFish run.

Create shared JSON golden cases from the existing frontend rule tests. Compare outcomes/reason codes across implementations for the overlapping supported subset, then add backend-specific ambiguity, currency, period, and validity cases. Do not compare localized message strings as the correctness contract.

## 11. Amendments and publication

1. Associate a corrigendum with a tender using explicit reference evidence; an ambiguous association stays unresolved.
2. Preserve the original notice, amendment documents, and listing observations as a snapshot set.
3. Resolve a targeted override only when its affected clause/date and precedence are clear. Retrieval time alone does not establish precedence.
4. Match clauses using stable identity plus document context. Classify added, changed, clearly superseded/removed, unchanged, and unresolved conditions.
5. Compare normalized meaning as well as raw hashes. A different PDF with identical requirements is a document change, not a readiness alert.
6. Re-evaluate affected predicates and aggregate against the whole effective set. A deadline extension must not erase an unrelated turnover blocker.
7. Commit the selected snapshot, conditions, changes, and evaluation publication atomically. Failed attempts leave the previous accepted data intact, with visible stale/current-coverage state.

Missing a notice in a bounded listing is not withdrawal evidence. A listing-only deadline edit must be recorded; if it conflicts with document evidence, return Review needed. A failed amendment download cannot be treated as an unchanged notice.

Deduplicate changes using tender, old/new snapshot, clause identity, and normalized before/after content. Repeating the same refresh must not create duplicate alerts or evaluations unnecessarily.

## 12. Frontend migration and compatibility

| Existing file/behavior | Planned change |
| --- | --- |
| `frontend/lib/auth-context.tsx` | Continue Firebase sign-in; obtain ID tokens for the API and replace direct Data Connect user upsert with `/me` |
| `frontend/components/workspace-provider.tsx` | Load/save business data through the API; keep collapsed-sidebar preference local |
| `frontend/lib/discovery-server.ts` | Retire after Python owns provider calls and recovery; prevent two active implementations submitting paid runs |
| `frontend/app/api/discovery/` | Temporarily translate to FastAPI refresh routes, then remove or retain documented compatibility wrappers |
| `frontend/lib/types.ts` | Generate/import OpenAPI-based contracts; adapt money and canonical IDs deliberately |
| `frontend/components/tender-explorer.tsx` | Use server pagination/search/readiness; show stale, processing, and coverage state distinctly |
| `frontend/components/tender-drawer.tsx` | Use real evidence links, versions, conditions, and backend findings; keep synthetic viewer limited to sample data |
| Profile, saved, source, and amendment screens | Persist through authenticated endpoints; show optimistic update rollback and actionable errors |

Migration order:

1. Keep the public landing and labelled sample workspace available without sign-in. Require Firebase identity before private writes and paid discovery.
2. Introduce an explicit backend-enabled feature flag and typed API client. Avoid a silent fallback from a failed authenticated API call to synthetic/live-looking local data.
3. Migrate `/me`, profile reads/writes, and bookmarks before switching discovery. Prove persistence across browser reloads and another browser session.
4. Offer a one-time, user-initiated local-workspace import. Use an import key to prevent duplicate profile versions/bookmarks.
5. Reject or separately namespace synthetic IDs. Resolve old `live-<run>-<index>` bookmark references against trusted source identities; ask for review on ambiguous matches rather than guessing by title.
6. Move provider credentials and collection ownership to Python, then switch job polling to backend state. Map all active pipeline stages to the current UI's running state until its types are expanded.
7. Replace sample evidence and changes with live backend data only when actual artifacts exist.
8. Retire legacy direct Data Connect business writes and shared-token discovery. Remove business facts from browser storage only after a successful import/read-back; preserve the user's ability to export before cleanup.

**Acceptance:** Profile changes and saved notices survive local-storage clearing after sign-in; user B never sees user A's imported data; closing the browser does not stop an active refresh.

## 13. Testing, evaluation, and CI

### 13.1 Required checks

| Layer | High-value cases |
| --- | --- |
| Domain | Exact boundary values; zero versus unknown; missing year; average versus sum; absent versus unknown certificate; invalid validity; passed/date-only deadline; incomplete and empty coverage |
| Authentication/authorization | Missing/expired/invalid identity; wrong project; another workspace's profile/job/bookmark/evidence; forbidden cancellation/deletion |
| API | Invalid request models; version conflicts; repeat bookmark PUT/DELETE; idempotency-key reuse with a different body; cursor/filter behavior |
| Provider | All lifecycle states; completed goal failure; malformed/empty/duplicate output; out-of-host links; 401/403/429; ambiguous submission; cancel/complete race |
| Worker/database | API/worker restart; lease expiry and fencing; two workers claiming the same job; duplicate completion delivery; provider slot exhaustion; no automatic resubmission of unknown attempts |
| Documents | Exact page/quote; multi-page clauses; scanned/corrupt/large PDF; redirected/private URL; same URL/new bytes; same bytes/new observation; parser-version changes |
| Amendments | Deadline-only change; unchanged control; formatting-only PDF change; conflicting dates; unresolved precedence; inaccessible new amendment; duplicate refresh |
| Integration | Profile → discovery → evidence → evaluation → amendment history; cache expiry at a clock boundary; browser closed while work continues |

Use real PostgreSQL for locking, uniqueness, JSONB, and migration tests. SQLite is not a substitute for the worker's queue and concurrency checks. Use fixture provider responses and HTTP mocks in normal CI, plus dependency overrides or the Auth Emulator for identity tests. Do not require production Firebase, AWS, or TinyFish credentials for pull-request checks.

### 13.2 Corpus and measurable release gates

- Freeze ten real text-based notices with source URLs, original hashes, document dates, field labels, and correct page spans.
- Label an original/amendment pair and at least one unchanged pair. Keep synthetic negative fixtures in a separate namespace.
- Target the pitch's ≥90% exact field extraction on the frozen ten-notice inventory, 100% correct source/page linkage for reported conditions, and zero missing-evidence cases silently marked Meets.
- Score non-null gold fields separately from missing-field detection; unextracted present values count as errors. Report denominators and development/held-out use.
- Record false/missed amendment alerts, provider/ingestion/evaluation latency, and restart recovery outcome. Small-sample results must not be presented as general production accuracy.

### 13.3 Extend the existing GitHub Actions workflow

Add backend jobs after the application/lockfile exist; do not commit a job that invokes nonexistent commands.

1. Set up the pinned Python version and a reviewed `uv` action/tool version.
2. Run `uv sync --frozen --all-groups`.
3. Run `uv run ruff check .`, `uv run ruff format --check .`, and `uv run mypy app`.
4. Start a PostgreSQL 17 service with test-only credentials and a health check.
5. Run `uv run alembic upgrade head` and migration/isolation tests, including a sentinel legacy schema that must remain unchanged.
6. Run `uv run pytest -q`; keep provider I/O mocked and time injectable.
7. Generate/check OpenAPI and compile the frontend against the generated client when contracts change.
8. Build the backend container and run an API/worker smoke flow against fixture discovery and local document storage.
9. Keep the existing frontend quality and production jobs. A separate, manually invoked live integration check may use staging credentials and an explicit run budget.

## 14. Implementation phases, dependencies, and exit criteria

Estimates are focused engineering time for the backend track, not a promise that all production infrastructure fits into the original 24-hour hackathon. Parallelize extraction/rules and frontend migration only after their contracts are stable.

| Phase | Work | Estimate | Exit criterion |
| --- | --- | --- | --- |
| 0 — Confirm boundaries | Verify source/account access, database host/access, Data Connect migration ownership, target runtime and provider adapter | 1–2 h | Written configuration choices; no assumed deployed resource |
| 1 — Scaffold and local services | Project/lockfile, settings, Compose DB, app factory, logging/errors, health/readiness, first migration | 2–3 h | Fresh checkout starts locally and migrates a blank database |
| 2 — Identity and persistent workspace | Firebase verification, workspace provisioning, profile versions, bookmarks, access tests, import contract | 4–5 h | Authenticated CRUD survives reload; cross-user access fails |
| 3 — Durable discovery | Jobs/attempts/leases, provider adapter, source policy, output validation, cancellation/reconciliation, fixture mode | 4–5 h | Restart during a run resumes without duplicate submission |
| 4 — Real PDF evidence | Safe downloader, immutable storage, hashes, parser artifacts, source-specific clause extraction | 5–7 h | One real document produces exact page-linked clauses; bad PDFs stay unresolved |
| 5 — Five rule groups | Decimal/period/date normalization, supplier fact provenance, coverage, immutable evaluations and clock expiry | 4–5 h | Golden rule cases and all missing-data safety checks pass |
| 6 — Amendments | Effective document sets, explicit overrides, meaningful diffs, atomic publication, deduplication | 3–4 h | A real historical pair and unchanged control produce correct history |
| 7 — Frontend cutover | Typed client/proxy, Firebase token forwarding, profile/bookmark import, API-driven evidence and job state | 3–4 h | One complete signed-in dashboard journey uses backend data |
| 8 — CI, benchmark, deployment | Backend CI, ten-notice evaluation, container/startup, staging migrations, restore and smoke rehearsal | 4–5 h | Staging flow, measurements, and rollback instructions recorded |

**Total planning range:** approximately 30–40 focused backend/integration hours. Suggested responsibility: backend/integration lead handles phases 0/1/3 and deployment; data/rules contributor handles 4/5/6; frontend contributor handles 7; validation contributor prepares corpus/tests throughout. These are proposed work boundaries, not assignments sent to teammates.

First useful vertical slice: phases 0/1, minimal authenticated profile, one durable fixture/live discovery job, one real PDF evidence span, and one supported turnover check. Then expand to all five checks before claiming full MVP acceptance. If time is short, cut additional sources, scheduling, and presentation polish rather than evidence provenance or missing-data handling.

## 15. Deployment, operations, and rollback

### Deployment sequence

1. Choose one database host and verify networking, TLS, migrations, backup permissions, and service region. If reusing Cloud SQL, validate the separate schema and compatible Data Connect migration mode on staging.
2. Build one pinned backend image; run the API and worker as separate services with different commands and restart policies.
3. Place the API behind HTTPS. Keep database access private/controlled and use a runtime role without migration DDL privileges.
4. Grant only required Firebase verification, object-storage, and secret access. Prefer workload identity/instance roles; keep any local credential file outside Git.
5. Apply migrations as a deployment step before routing traffic. Seed only source configuration in production, never demo suppliers or synthetic notices.
6. Deploy the API and worker, configure the Next.js proxy, and smoke-test with a staging account.
7. Perform one explicitly budgeted real TinyFish run, retain its run ID/source evidence, and verify it continues after closing the browser.
8. Run the amendment/unchanged checks, then enable backend mode for the intended workspace.

The original target is Amplify/EC2/S3/RDS/Secrets Manager/CloudWatch. Reusing the current Cloud SQL configuration changes that database/network topology; document the selected arrangement and update the architecture diagram before claiming deployment completion. The backend application code must not depend on a particular managed PostgreSQL brand.

### Operational signals

Log request, workspace, application job, provider attempt/run, document hash, profile version, parser version, and rule version as correlation fields. Redact tokens, secret values, and private fact payloads. Measure queue age, heartbeat/lease failures, duplicate avoidance, provider error category, extraction coverage, document/condition changes, and stage latency.

Alert first on stuck/unknown submissions, missing worker heartbeats, repeated source failures, and an increase in unresolved extraction. Record real provider usage; wall-clock limits and a five-notice cap do not constitute a precise monetary spending cap.

### Rollback and recovery

- Roll back application images independently of stored evidence. Keep backward-compatible migrations during the first releases.
- Restore the database and verify referenced immutable object blobs are available; test the restore path before relying on backups.
- Pause new provider submissions during an incident, but retain/reconcile known run IDs. Never resolve an unknown run by deleting its record and retrying.
- If frontend cutover must be disabled, show a labelled read-only/sample experience. Do not silently treat stale browser facts as the authoritative persistent workspace.

## 16. Backend definition of done

- [ ] A fresh checkout can install locked dependencies, start PostgreSQL, migrate, seed, and run API plus worker from the README.
- [ ] Firebase identity is verified server-side and every private resource is workspace-scoped.
- [ ] Profiles and bookmarks persist outside browser storage, with explicit migration/import behavior.
- [ ] Python owns TinyFish collection; the Next.js implementation cannot submit a second run in parallel.
- [ ] A real, application-initiated provider run is recorded and survives an API/worker restart.
- [ ] Original PDFs, hashes, parse versions, exact pages/quotes, and provenance are retained.
- [ ] All five condition groups handle uncertainty, applicability, exact periods/units, and time boundaries conservatively.
- [ ] Evaluations are reproducible and an expired/stale pass is never presented as current.
- [ ] A meaningful amendment comparison and an unchanged control work without duplicate alerts.
- [ ] The ten-notice extraction/evidence/safety targets are measured and failures are reported honestly.
- [ ] Backend CI and the existing frontend checks pass with no real paid provider call.
- [ ] The selected database host, Data Connect ownership boundary, deployment procedure, and restore/recovery behavior are documented and smoke-tested.

## 17. Source notes

Repository findings in section 1 were checked on 24 October 2026. The external references linked above are primary documentation read during planning. Firebase's current documentation uses the name SQL Connect; repository paths and generated code still use Data Connect. This plan does not require a directory rename.

No Python server, dependency install, database migration, Firebase deployment, cloud resource, or paid provider run was created by writing this plan. Infrastructure/account availability and corpus quality remain implementation gates, not assumed completed work.
