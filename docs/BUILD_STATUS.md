# TenderLens — Current Build Status

**Updated:** 24 October 2026. This file records implementation progress separately from the original target architecture and 24-hour plan.

## Implemented

| Area | Current behavior |
| --- | --- |
| Landing | Product introduction, sample product preview, how-it-works sections, workspace entry points |
| Dashboard | Collapsible sidebar, mobile navigation, persistent shared workspace shell |
| Tender review | Search, category/readiness filters, sort, saved notices, shortlist JSON export |
| Supplier profile | Editable facts, tri-state certificates, exact annual financial periods, local browser persistence |
| Rules | Five deterministic sample check types; known failures block; missing facts/evidence stay unresolved; incomplete coverage cannot pass |
| Evidence | Native modal drawer, expandable findings, source links, page-linked synthetic document viewer |
| Changes | Two explicitly synthetic before/after examples |
| TinyFish | Server-only async submission/polling, source URL validation, saved local run IDs, signed access cookie, duplicate-start control, bounded run time, explicit unknown-submission handling |
| Architecture | Mermaid Charts output, saved `.mmd` source, rendered `/architecture` page |

## Current limits and next work

- The eight default notices and all displayed sample clauses are synthetic. The sample clock is fixed at 24 October 2026.
- Live discovery is wired to the documented TinyFish REST API. No metered real run was started during this UI implementation; account access and source accessibility still need a live smoke check.
- Live notice deadlines remain unparsed text; no precise timestamp, category, value, relevance score, or readiness condition is invented.
- Live PDF download/extraction, real clause evidence, document hashing/versioning, effective amendment resolution, and the ten-notice benchmark are not implemented.
- Profile and bookmarks are browser-local. Discovery records use the local filesystem, and polling runs while a workspace is open. This is not the proposed durable production worker.
- FastAPI, PostgreSQL, S3, production organisation authentication, and AWS deployment are planned. Hosted metered discovery requires the server access token.
- The repository starter is Next.js 16.4.3, React 19.3.0; hosting support must be checked before AWS deployment.

## Verification

- GitHub Actions CI is configured for pushes, pull requests, and manual dispatch, with separate quality and production build/smoke jobs on Node.js 24. The production job uses non-sensitive placeholder Firebase configuration and has no TinyFish credentials.

- ESLint and TypeScript checks passed.
- Seventeen behavior tests passed: missing financial years, unknown versus absent certificates, zero funding, evidence requirements, deadline boundaries, incomplete coverage, aggregate status precedence, live result schema checks, no-match semantics, duplicate limits, and source URL restrictions.
- Production build generated the landing, dashboard routes, architecture page, sample documents, and dynamic discovery routes.
- HTTP smoke checks cover page content and API configuration, cross-origin submission rejection, and signed job access.
- Mermaid grammar was checked with the installed Mermaid parser; a sanitizer stub was used only for the server-side syntax check because the parser normally expects a browser DOM. The application uses Mermaid's strict security mode.
- Browser visual/interaction review was unavailable because the computer-use runtime reported no connected browsers. Responsive styles and interaction handlers are implemented, but an actual desktop/mobile browser review remains to be done.

See the root [README](../README.md) for local setup and commands.
