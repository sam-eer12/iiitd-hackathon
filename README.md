# TenderLens

Find, review and buy in one supplier workspace. TenderLens keeps Google sign-in, supplier profiles, DigiLocker and TinyFish discovery, with a clearly labelled hackathon demo checkout and saved receipts.

**Final flow:** Google sign-in → save supplier profile → DigiLocker → fetch tenders with TinyFish → review official documents → demo checkout → receipt in My tenders. DigiLocker remains optional for the demo; unverified identities stay labelled unverified. See the [final workflow implementation plan](docs/IMPLEMENTATION_PLAN.md).

## Run locally

Requires Node.js 22.21+ and npm. The application lives in `frontend/`.

```sh
cd frontend
npm install
npm run dev
```

Open [the landing page](http://localhost:3000), [the dashboard](http://localhost:3000/dashboard), or [the architecture diagram](http://localhost:3000/architecture).

Use `localhost` for Google sign-in: it is an authorized Firebase domain for this project. In development, browser visits to `127.0.0.1` redirect to `localhost`, preserving the port, path, and query. Additional hosted domains must be added in Firebase Authentication > Settings > Authorized domains.

## Current implementation

- Responsive landing page and dashboard with a collapsible desktop sidebar and mobile navigation.
- Searchable tender list, open/closed/deadline-unconfirmed filters, sorting and save-for-later bookmarks.
- Existing Google sign-in, editable supplier profile and DigiLocker/EntityLocker document verification.
- Simplified review with official PDFs, original deadline text, collection time and amendment links.
- Demo checkout with simulated success/failure, retryable failures and one durable order per supplier and tender.
- My tenders at `/dashboard/purchases` with account-owned history, resumable checkout and downloadable demo receipts.
- Browser persistence for profile, bookmarks, sidebar preference, and discovery results.
- Server-only TinyFish async discovery adapter with bounded runs, structured result validation, exact source-host validation, signed job access, and local run records.
- Simplified supplier workflow and application architecture rendered with Mermaid in the app.

The default workspace contains **five real IIIT-Delhi notices collected with TinyFish on 24 October 2026**. The recorded API result, collection time, and provider run ID are in `frontend/lib/data/iiitd-tenders.json`. The listing includes recently closed notices with their actual deadlines. No tender prices, eligibility clauses, or amendment changes are invented. Synthetic fixtures remain available only for rule tests and explicitly labelled sample-document routes.

The dashboard loads the latest completed source snapshot from `GET /api/tenders`, falling back to the recorded real snapshot. Completed runs update the catalog; failed refreshes preserve it. Browser storage retains the supplier profile and bookmarks, and stable source identities preserve bookmarks across refreshes. Signed-in profiles, document verification and demo purchases use FastAPI in `backend/`. Existing local and remote TinyFish discovery modes remain supported. Advanced readiness scoring and amendment comparison are outside the simplified primary flow.

Demo checkout requires the existing backend and PostgreSQL database. Apply the new migration before starting the API:

```sh
cd backend
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The displayed ₹499 is a fixed simulated amount, not an issuer fee. Actually charged: ₹0. No banking data, bid submission, exclusive reservation or contract award is involved. Official documents remain public. Orders and receipts are saved in PostgreSQL, not browser storage; an unavailable backend shows an error instead of a success receipt.

## Enable TinyFish discovery

Copy `frontend/.env.example` to `frontend/.env.local` and set `TINYFISH_API_KEY`, or provide that variable in the app server's environment. Restart the server after changing configuration.

Visit **Connected sources** in the dashboard to inspect configuration and start a live run. Runs are metered against the configured TinyFish account; no run starts automatically when a page opens. The Codex MCP connection is independent of the application API configuration.

For hosted use, also configure `DISCOVERY_ACCESS_TOKEN` and enter it on Connected sources. Without that setting, live submissions are restricted to local development. API keys remain server-side. Never put them in `NEXT_PUBLIC_*` variables or commit `.env.local`.

The current adapter allows only `iiitd.ac.in` and `www.iiitd.ac.in` over HTTPS. A legitimate document on another host needs explicit source-adapter review before it can be accepted.

Run records and the latest successful catalog are stored under the ignored `frontend/.data/discovery/` directory. An interrupted submission can become `submission_unknown`; the app blocks another submission until an operator reconciles the correlation marker/run in TinyFish. Do not clear that record and blindly retry: a metered run may already exist. Polling resumes when the workspace is open; a production background worker is still planned.

## Checks and production build

```sh
cd frontend
npm run lint
npm test
npm run typecheck
npm run format:check
npm run smoke # with the development server running
npm run build
npm start
```

Development uses `.next/`; production build/start use `.next-production/` so the two caches do not conflict. The provided starter uses Next.js 16.4.3. Recheck hosting compatibility before the planned Amplify deployment; the original architecture proposal had assumed a supported Next.js 15 release.

## Project documents

GitHub Actions runs on pushes, pull requests, and manual dispatches. It uses Node.js 24, installs from the frontend lockfile, and runs lint, generated route type checks, behavior tests, formatting, a production build, and HTTP smoke tests. CI uses placeholder Firebase configuration and never starts a paid TinyFish discovery run; repository secrets are not required. The workflow is [CI](.github/workflows/ci.yml).

- [Product requirements](docs/PRD.md)
- [Architecture and integration contracts](docs/ARCHITECTURE.md)
- [Full architecture Mermaid source](docs/architecture.mmd)
- [Final simplified workflow implementation plan](docs/IMPLEMENTATION_PLAN.md)
- [Detailed backend implementation plan](backend/IMPLEMENTATION_PLAN.md)
- [Current build status and verification](docs/BUILD_STATUS.md)

Based on the TenderLens pitch for HackIIITD 2026, Team IDK.
