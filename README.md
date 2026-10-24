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
- Editable supplier profile and deterministic sample checks for turnover, experience, certificates, EMD capacity, and deadline.
- Evidence drawer, linked synthetic source documents, and illustrative amendment history.
- Browser persistence for profile, bookmarks, sidebar preference, and discovery results.
- Server-only TinyFish async discovery adapter with bounded runs, structured result validation, exact source-host validation, signed job access, and local run records.
- Complete target architecture rendered with Mermaid in the app and generated through Mermaid Charts.

The default workspace contains **eight synthetic notices** and uses a **24 October 2026 demo clock**. They demonstrate the interface and rules; they are not actual IIIT-Delhi notices. The ten-notice benchmark described in the pitch has not been performed.

Live discovery returns actual source observations and links. Its notices stay **Review needed** because live PDF extraction, condition verification, and amendment comparison are not implemented yet. The proposed FastAPI backend, durable worker, PostgreSQL/S3 persistence, and AWS deployment remain the next implementation phase. Browser storage and local discovery files are a development foundation, not the planned production persistence layer.

## Enable TinyFish discovery

Copy `frontend/.env.example` to `frontend/.env.local` and set `TINYFISH_API_KEY`, or provide that variable in the app server's environment. Restart the server after changing configuration.

Visit **Connected sources** in the dashboard to inspect configuration and start a live run. Runs are metered against the configured TinyFish account; no run starts automatically when a page opens. The Codex MCP connection is independent of the application API configuration.

For hosted use, also configure `DISCOVERY_ACCESS_TOKEN` and enter it on Connected sources. Without that setting, live submissions are restricted to local development. API keys remain server-side. Never put them in `NEXT_PUBLIC_*` variables or commit `.env.local`.

The current adapter allows only `iiitd.ac.in` and `www.iiitd.ac.in` over HTTPS. A legitimate document on another host needs explicit source-adapter review before it can be accepted.

Run records are stored under the ignored `frontend/.data/discovery/` directory. An interrupted submission can become `submission_unknown`; the app blocks another submission until an operator reconciles the correlation marker/run in TinyFish. Do not clear that record and blindly retry: a metered run may already exist. Polling resumes when the workspace is open; a production background worker is still planned.

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
