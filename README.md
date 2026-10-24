# TenderLens

Find the tender worth your time. TenderLens helps small suppliers discover relevant notices, compare supported requirements with their profile, and inspect the evidence behind a readiness result.

## Run locally

Requires Node.js 22.21+ and npm. The application lives in `frontend/`.

```sh
cd frontend
npm install
npm run dev
```

Open [the landing page](http://localhost:3000), [the dashboard](http://localhost:3000/dashboard), or [the architecture diagram](http://localhost:3000/architecture).

## Current implementation

- Responsive landing page and dashboard with a collapsible desktop sidebar and mobile navigation.
- Searchable tender list, category/readiness filters, sorting, bookmarks, and JSON shortlist export.
- Editable supplier profile and conservative readiness labels; real notices stay Review needed until their clauses are verified.
- Evidence drawer with official tender PDFs, original deadline text, observation timestamps, and collected amendment links.
- Browser persistence for profile, bookmarks, sidebar preference, and discovery results.
- Server-only TinyFish async discovery adapter with bounded runs, structured result validation, exact source-host validation, signed job access, and local run records.
- Complete target architecture rendered with Mermaid in the app and generated through Mermaid Charts.

The default workspace contains **five real IIIT-Delhi notices collected with TinyFish on 24 October 2026**. The recorded API result, collection time, and provider run ID are in `frontend/lib/data/iiitd-tenders.json`. The listing includes recently closed notices with their actual deadlines. No tender prices, eligibility clauses, or amendment changes are invented. Synthetic fixtures remain available only for rule tests and explicitly labelled sample-document routes.

The dashboard loads the latest completed source snapshot from `GET /api/tenders`, falling back to the recorded real snapshot. Completed application runs update the shared catalog; failed refreshes preserve it. Browser storage retains the supplier profile and bookmarks, and stable source identities preserve bookmarks across refreshes. Old sample workspaces migrate to real notices automatically. Live PDF clause verification and amendment comparison remain pending in this dashboard. The separate FastAPI API and worker are in `backend/`; the dashboard currently uses the Next.js discovery routes and local server files.

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
- [24-hour implementation plan](docs/IMPLEMENTATION_PLAN.md)
- [Detailed backend implementation plan](backend/IMPLEMENTATION_PLAN.md)
- [Current build status and verification](docs/BUILD_STATUS.md)

Based on the TenderLens pitch for HackIIITD 2026, Team IDK.
