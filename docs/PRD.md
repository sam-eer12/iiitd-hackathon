# TenderLens: simplified supplier experience

Updated 25 October 2026 after round 2 mentoring.

## Problem

Small suppliers need an easy way to find an official tender, review its documents and follow through with a clear purchase journey.

## Product promise

Find, review and buy in one supplier workspace. The hackathon build demonstrates buying through an explicitly simulated checkout.

## Primary user journey

Google sign-in → supplier profile → DigiLocker → TinyFish discovery → review official documents → demo checkout → receipt in My tenders.

DigiLocker stays available for PAN identity verification; EntityLocker supports GST. The demo accepts an unverified identity while preserving that label. Verification never implies tender eligibility.

## Core experience

| Screen | Supplier action | Result |
| --- | --- | --- |
| Supplier profile | Save business, contact, email and categories; optionally complete existing financial fields and verification | Account-owned supplier details |
| Discover tenders | Fetch with TinyFish, search, filter by closing status | Real official notices with dated source provenance |
| Tender review | Read title, issuer, deadline, PDFs and amendment links | An informed manual review, with save or checkout actions |
| Demo checkout | Confirm review/demo terms and simulate a payment outcome | Retryable failure or successful demo purchase |
| My tenders | Resume review/checkout, open documents, download receipts | Durable purchase history in the supplier account |

## Required behavior

- Preserve Google sign-in, supplier profile creation, TinyFish collection and DigiLocker integration.
- Keep the primary tender review on one screen; remove automatic readiness scoring from this journey.
- Preserve original source dates and links. Do not infer prices, eligibility or amendment changes.
- Block checkout for closed or unknown deadlines.
- Require a signed-in account, a complete saved basic profile and explicit review/demo acknowledgements.
- Charge no money and collect no banking data.
- Use a fixed ₹499 simulated amount, clearly separate from the issuer's fee; actually charged is ₹0.
- Persist orders in PostgreSQL, scope all access to the workspace and keep one order per tender per workspace.
- A successful order has one immutable demo receipt. Failures may be retried; repeated requests cannot undo success.
- Recover receipts after reload and even after the notice disappears from the latest discovery snapshot.
- Handle unavailable backend/source services with visible errors and no fabricated success.

## Outside this release

Real payment processing, automated bid submission, exclusive tender reservations, contract awards, automatic eligibility decisions, OCR, new discovery sources, advanced amendment comparison and new infrastructure.

Save for later is a personal bookmark. A demo purchase does not reserve or win a tender. Existing backend document/rule modules remain available for later work but are not prerequisites for reviewing or buying in the demo.

## Success criteria

A mentor can follow one supplier from sign-in through review to a saved demo receipt, including a failed payment and retry, without needing an explanation of scoring engines or document-processing pipelines.

See the [final implementation plan](IMPLEMENTATION_PLAN.md), [architecture](ARCHITECTURE.md) and [verified build status](BUILD_STATUS.md).
