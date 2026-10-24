# TenderLens — Product Requirements Document

**Status:** Product specification; a local UI foundation is implemented. See [current build status](BUILD_STATUS.md) for verified scope and pending backend work.  
**Planning date:** 24 October 2026  
**Team:** IDK — Sameer Gupta, Trisha, Tripti, Sunil  
**Product promise:** Find the tender worth your time.

This PRD is based on the nine-page [TenderLens pitch](../TenderLens%20Idea%20Submission%20%281%29%20%281%29.pdf), including the review journey pictured on slide 4. The pitch is the source of product scope; technical decisions added here are proposals for implementation. Read alongside [Architecture](ARCHITECTURE.md) and [Implementation Plan](IMPLEMENTATION_PLAN.md).

## 1. Problem and intended outcome

Small suppliers spend time discovering procurement notices, opening several PDFs, checking eligibility, and returning to the source for amendments. A notice can match their products while still containing a disqualifying turnover, experience, certificate, deposit, or deadline requirement. A corrigendum can change a previously reviewed condition.

TenderLens helps a supplier shortlist relevant notices, compare explicitly supported requirements with its profile, inspect the exact supporting clauses, and see what changed after a refresh. The supplier remains responsible for deciding whether to bid.

The distinguishing feature is traceability: every extracted condition has document evidence, every evaluated result has a reason, and every material amendment has a before/after record. Product relevance and bid readiness remain separate.

## 2. Users and jobs to be done

| User | Situation | Job to be done |
| --- | --- | --- |
| Primary: small lab-equipment supplier | Sells to colleges with a lean team and no dedicated bid analyst | Identify relevant tenders and understand blockers before investing in a bid |
| Secondary: local electronics or IT supplier | Encounters similar institutional procurement requirements | Reuse its capability profile and review changed conditions efficiently |
| Demo operator / reviewer | Maintains a small, labelled evaluation corpus | Run discovery, inspect provenance, and distinguish live results from fixtures |

Core user stories:

- As a supplier, I can enter my capabilities once and compare them with multiple notices.
- As a supplier, I can distinguish a product match from a supported readiness result.
- As a supplier, I can open the source clause behind a result and understand the comparison.
- As a supplier, I can see a changed deadline or condition without losing the earlier version.
- As a supplier, I can tell when information is missing, stale, unreadable, or manually supplied.

## 3. MVP scope and boundaries

The pitch commits to **one source, ten manually reviewed notices, five condition types, and one amendment comparison**, built by four people in 24 hours.

| Included in the MVP | Deferred |
| --- | --- |
| IIIT-Delhi public tender source, subject to a live access check | Universal procurement portal coverage |
| TinyFish Agent API discovery and refresh | CAPTCHA-dependent or authenticated portal workflows |
| Up to five selected notices per discovery run | Exhaustive crawling or guaranteed discovery of every tender |
| A ten-notice evaluation corpus from dated source documents | Large-scale accuracy claims |
| Supplier profile and editable capability facts | Multi-organisation accounts and production identity management |
| Text-based PDF extraction with page references | OCR and general scanned-document understanding |
| Deterministic checks for turnover, experience, certificates, deposit, deadline | Complex exemptions, consortium rules, and arbitrary legal interpretation |
| Relevant shortlist, evidence view, and amendment history | Bid generation, submission, payments, or automated bid decisions |
| User-triggered refresh and visible freshness | Scheduled alerts, email, WhatsApp, and continuous monitoring |
| Labelled cached replay and manual PDF upload fallback | Presenting fallback data as a successful live collection |
| Next.js UI, Python backend, PostgreSQL, S3, proposed AWS deployment | SQS-based distributed workers and multi-region operation |

Five notices is a per-run collection bound, not the benchmark size. The ten-notice benchmark can use multiple saved batches or archived public documents. Historical and synthetic examples must be labelled; do not claim that ten active matching tenders are currently available.

## 4. Product journey and screens

1. **Supplier profile:** enter categories, financial periods and turnover, completed work, certificates, and deposit capacity. Save a versioned profile.
2. **Tender shortlist:** start a source refresh, see its progress, then review relevant notices with separate relevance and readiness labels.
3. **Clause evidence:** select a notice and inspect each requirement, the corresponding supplier fact, the comparison, and the source PDF page.
4. **Amendment history:** refresh watched notices, inspect before/after values and citations, then review the updated readiness result.

| Screen | Required content and actions |
| --- | --- |
| Profile | Company name; categories/keywords; turnover by financial year and currency; work history; certificate details and validity; available deposit amount; save and validation feedback |
| Shortlist | Title, issuer/reference when available, source link, relevance reason, deadline text, readiness, freshness, changed-condition count, refresh control, run progress |
| Tender detail | Five condition groups; every discovered requirement within each group; requirement versus supplier facts; plain-language reason; unresolved coverage gaps; document list |
| Evidence panel | Exact clause text, clause label if present, physical PDF page number, document version/hash, retrieval time, original URL, archived PDF link |
| Changes | Old/new values and evidence, observed time, published amendment date if known, affected checks, previous/current readiness |
| Operational states | Empty results, source unavailable, run failed, stale snapshot, unreadable PDF, missing profile fact, manual upload, fixture replay |

Use the slide 4 layout as the initial interaction reference. Its sample turnover and date values are synthetic. In particular, do not treat “three years” as interchangeable with “three-year average”; the original clause must establish the basis.

## 5. Functional requirements

| ID | Priority | Requirement | Acceptance criterion |
| --- | --- | --- | --- |
| FR-01 | P0 | Save a supplier profile with explicit units, periods, and unknown values | Editing the profile creates a new version and triggers local re-evaluation without another TinyFish run |
| FR-02 | P0 | Discover public notices through TinyFish | At least one real application-initiated Agent API run is recorded with its provider run ID and validated result |
| FR-03 | P0 | Preserve discovery provenance | Every accepted notice links to its source observation, retrieval time, collection mode, and available document/amendment URLs |
| FR-04 | P0 | Rank relevance separately | Category/keyword matches explain the ranking and never determine readiness |
| FR-05 | P0 | Extract PDF clauses with page-level evidence | Every displayed extracted condition opens a stored source document and its cited page |
| FR-06 | P0 | Evaluate five supported condition types | Rules return Meets, Blocked, or Review needed with a reason and the compared values |
| FR-07 | P0 | Preserve uncertainty | Missing facts, unreadable documents, unknown periods, ambiguous exceptions, and conflicting amendments never silently pass |
| FR-08 | P0 | Track versions and amendments | A changed condition produces an old/new comparison and re-evaluates the affected tender; unchanged content produces no duplicate alert |
| FR-09 | P0 | Expose collection and processing state | The user can distinguish provider execution, PDF processing, successful publication, and failure |
| FR-10 | P0 | Support explicit fallbacks | Cached and manually uploaded evidence remains clearly labelled with its original date and provenance |
| FR-11 | P0 | Keep history reproducible | A historical result identifies the profile version, tender document set, evaluation time, and rule version used |
| FR-12 | P0 | Protect the API and stored evidence | The TinyFish key stays on the backend; refresh/upload endpoints require a demo session; source downloads are allowlisted |
| FR-13 | P1 | Add shortlist filters and presentation polish | Filter by readiness, category, freshness, or changed status without altering underlying evaluations |

P0 is required for the complete MVP. P1 begins only after the end-to-end evidence and amendment flows work.

## 6. Supplier facts and readiness semantics

The profile stores factual inputs, not an AI-generated assertion of eligibility:

- **Turnover:** annual values, currency, exact financial-year labels, and whether supporting evidence is available. Compute averages only for the exact requested years.
- **Experience:** category, customer, completion date, order value/currency, and whether completion evidence is available. The MVP supports explicit counts/value thresholds and configured category matches; ambiguous “similar work” stays for review.
- **Certificates:** type, issuer if relevant, present/absent/unknown, validity dates, and evidence reference. Uncertain applicability or exemption remains unresolved.
- **Deposit:** available amount and currency. Comparing this with EMD indicates stated funding readiness, not that a deposit has been paid or a guarantee accepted.
- **Deadline:** comes from tender evidence and is checked against the evaluation clock. Certificate validity and other date-sensitive facts are rechecked when time advances.

### Per-condition result

| Result | Meaning |
| --- | --- |
| **Meets** | The supported comparison succeeds using an unambiguous requirement, sufficient supplier facts, matching units/periods, and valid evidence |
| **Blocked** | An unambiguous, applicable mandatory condition fails against known facts |
| **Review needed** | Evidence or a supplier fact is missing; text is unreadable; scope, applicability, period, timezone, or amendment precedence is unresolved |

Explicit non-applicability or waiver is recorded separately with evidence; it is never inferred from an absent field. The UI must say **“Meets checked conditions”**, not “Eligible” or “Guaranteed to qualify.”

### Aggregate result

Evaluate each currently supported condition, then apply:

1. A confirmed failure of a current mandatory condition yields **Blocked**; also show any unresolved issues.
2. Otherwise, any unresolved condition, incomplete document coverage, or missing required comparison yields **Review needed**.
3. Otherwise, **Meets checked conditions** is allowed only when at least one applicable check exists, all applicable checks pass, and coverage has been accounted for.

An unseen or unreadable amendment can invalidate an old condition. When supersession is uncertain, retain the old evaluation as history and show the current result as Review needed. A document with no extracted conditions does not pass by default. For each of the five groups, record extracted requirements, an evidenced non-applicability decision, or a coverage gap. Requirements outside the supported groups remain visible as review items when identified.

Do not equate a source refresh failure with an eligibility failure. Display the last evaluation as a dated historical result plus a stale/failure banner; do not present it as freshly verified.

## 7. Amendment behavior

- Track both newly linked corrigenda and changed bytes at an existing PDF URL.
- Record listing-only deadline changes as observations; if they conflict with PDF evidence, flag the conflict rather than silently choose one.
- Apply a corrigendum only when its tender identity and affected clause or date are clear. Retrieval time alone does not establish legal precedence.
- Show when a document changed but no supported condition changed; do not turn formatting-only changes into readiness alerts.
- Recompute only affected conditions when safe, then aggregate against the complete current set. Profile edits and clock changes can also trigger re-evaluation.
- A notice disappearing from a bounded listing response is not proof of withdrawal or cancellation.
- A historically replayed amendment can demonstrate the comparison, but must not be described as a newly detected live change.

## 8. Acceptance targets and measurement

These are **targets from the pitch, not achieved results**.

| Metric | Target / method |
| --- | --- |
| Exact field extraction | At least 90% on ten manually labelled notices; freeze the field inventory before scoring |
| Evidence coverage | 100% of reported extracted conditions reference the correct source document and page |
| Missing-evidence safety | Zero missing-evidence cases silently marked Meets |
| Amendment demonstration | At least one before/after comparison with traceable evidence and an explained readiness outcome |
| False/missed amendment alerts | Report both counts against labelled document pairs; include an unchanged control |
| Refresh latency | Record provider, download, extraction, evaluation, and end-to-end durations; report measured values |
| Review-time benefit | Compare completion time for the same review task manually and with TenderLens; report sample size and limitations |

For exact extraction, score non-null gold fields separately from correct detection of missing fields so null-heavy records cannot inflate accuracy. Include incorrect values and unextracted present values as errors. Label monetary amount/currency, turnover period/basis, dates, and condition evidence. Report per-field and overall results, the denominator, and which examples were used during development. Synthetic safety tests supplement the ten real-notice corpus and do not count toward its accuracy target.

## 9. Non-functional requirements

- Long-running discovery must not hold a browser request open. Return a job ID and show progress.
- A backend restart must preserve provider run IDs, jobs, and already-published snapshots.
- Preserve immutable PDF bytes and historical evaluations; never rewrite old evidence in place.
- Keep network retries, run duration, concurrent runs, file size, and page count bounded.
- Keep status text and icons alongside colour; make primary controls keyboard accessible and tables readable on smaller screens.
- Use synthetic supplier data for the shared hackathon demo. Production handling of confidential supplier documents requires a later access-control design.
- The demo must run locally; AWS deployment must be separately verified before claiming it is live.

## 10. Risks, assumptions, and release gates

| Risk / assumption | Control or decision |
| --- | --- |
| Source content is inaccessible or changed | First-three-hours gate: inspect the live page with TinyFish and verify PDF links. A planning-time page fetch exposed navigation but not usable notice content; access is not yet proven |
| Fewer than ten suitable active notices | Use dated archived public notices for the benchmark; show historical status explicitly |
| API key, quota, or account capability unavailable | Check at kickoff; preserve labelled snapshots. A replay alone does not satisfy the real TinyFish integration gate |
| Scanned PDFs or ambiguous conditions | Review needed plus source evidence; manual upload only helps when a usable text PDF is available |
| Incomplete extraction creates false confidence | Coverage accounting, negative fixtures, and conservative aggregation |
| AWS setup consumes the final hours | Start infrastructure prerequisites early; keep the local demo runnable throughout |
| Short hackathon schedule | Freeze source coverage and five rule types; postpone cosmetic and expansion work |

No live Agent run, application benchmark, or AWS deployment was performed while writing the original planning documents. The later UI build and its verification are recorded in [Build Status](BUILD_STATUS.md). Current account entitlements, usable tender corpus, and infrastructure readiness still need live verification.

## 11. Source and pitch traceability

| Pitch pages | Requirement reflected here |
| --- | --- |
| 1–2 | Product promise, problem, primary and secondary users |
| 3–5 | Profile → discovery → evidence → rules → shortlist; three statuses; four-screen review journey |
| 6–7 | AWS stack, TinyFish as collection layer, server-only credentials, validated runs |
| 8 | Four-person ownership, 24-hour scope, ten notices, five checks, one amendment, deferred OCR |
| 9 | Accuracy, evidence coverage, missing-data safety, amendment and latency measurements |

External references: [IIIT-Delhi tender page](https://iiitd.ac.in/tenders), [TinyFish Agent API](https://docs.tinyfish.ai/agent-api/reference), and [TinyFish run semantics](https://docs.tinyfish.ai/key-concepts/runs), checked during planning on 24 October 2026. Implementation-specific source references are in the architecture document.
