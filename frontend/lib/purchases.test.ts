import assert from "node:assert/strict";
import { test } from "node:test";
import { readFileSync } from "node:fs";
import { validateDiscoveryResult } from "./discovery-validation.ts";
import {
  formatDemoAmount,
  purchaseSnapshot,
  sourceReviewVersion,
  tenderAvailability,
} from "./purchases.ts";

const recorded = JSON.parse(
  readFileSync(new URL("./data/iiitd-tenders.json", import.meta.url), "utf8"),
);
const tender = validateDiscoveryResult(
  recorded.result,
  recorded.retrievedAt,
  recorded.providerRunId,
)[0];

test("only a strictly future confirmed deadline permits checkout", () => {
  const deadline = new Date(tender.deadline!);
  assert.equal(
    tenderAvailability(tender, new Date(deadline.getTime() - 1)),
    "open",
  );
  assert.equal(tenderAvailability(tender, deadline), "closed");
  assert.equal(
    tenderAvailability(tender, new Date(deadline.getTime() + 1)),
    "closed",
  );
  assert.equal(tenderAvailability({ deadline: null }, deadline), "unknown");
  assert.equal(
    tenderAvailability({ deadline: "invalid" }, deadline),
    "unknown",
  );
});

test("source edits invalidate review but recollection and document ordering do not", () => {
  const version = sourceReviewVersion(tender);
  assert.equal(
    version,
    sourceReviewVersion({ ...tender, retrievedAt: "2099-01-01T00:00:00Z" }),
  );
  for (const change of [
    { title: "Changed specification" },
    { deadline: "2099-01-01T00:00:00Z" },
    { deadlineText: "Extended" },
    { pdfUrls: ["https://iiitd.ac.in/new.pdf"] },
    { amendmentUrls: ["https://iiitd.ac.in/amendment.pdf"] },
  ])
    assert.notEqual(version, sourceReviewVersion({ ...tender, ...change }));
  const two = {
    ...tender,
    pdfUrls: ["https://iiitd.ac.in/a.pdf", "https://iiitd.ac.in/b.pdf"],
  };
  assert.equal(
    sourceReviewVersion(two),
    sourceReviewVersion({ ...two, pdfUrls: [...two.pdfUrls].reverse() }),
  );
});

test("purchase snapshots preserve official links without inventing eligibility or a fee", () => {
  const snapshot = purchaseSnapshot(tender);
  assert.equal(snapshot.id, tender.id);
  assert.deepEqual(snapshot.pdfUrls, tender.pdfUrls);
  assert.equal(snapshot.deadlineText, tender.deadlineText);
  assert.equal("conditions" in snapshot, false);
  assert.equal("value" in snapshot, false);
  assert.equal("fee" in snapshot, false);
  assert.equal(formatDemoAmount(49900), "₹499");
});
