import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import {
  validateDiscoveryResult,
  validateSourceUrl,
} from "./discovery-validation.ts";

const notice = {
  notice_id: null,
  title: "Visible notice",
  source_url: "https://iiitd.ac.in/tenders",
  deadline_text: null,
  pdf_urls: ["https://iiitd.ac.in/sites/default/files/test.pdf"],
  amendment_urls: [],
};
const parse = (value: unknown) =>
  validateDiscoveryResult(value, "2026-10-24T09:00:00Z", "test-run");
test("a valid live result preserves missing fields and has no fabricated clauses", () => {
  const [result] = parse({
    outcome: "success",
    failure_reason: null,
    notices: [notice],
  });
  assert.equal(result.provenance, "live");
  assert.equal(result.deadline, null);
  assert.equal(result.deadlineText, null);
  assert.deepEqual(result.conditions, []);
  assert.equal(result.relevance, null);
});
test("explicit no matches is valid and returns no sample notices", () => {
  assert.deepEqual(
    parse({ outcome: "no_matches", failure_reason: null, notices: [] }),
    [],
  );
});
test("provider completion cannot mask a goal failure", () => {
  assert.throws(
    () =>
      parse({
        outcome: "failed",
        failure_reason: "Source blocked",
        notices: [],
      }),
    /could not inspect/,
  );
});
test("inconsistent success and no-match outcomes fail validation", () => {
  assert.throws(() =>
    parse({ outcome: "success", failure_reason: null, notices: [] }),
  );
  assert.throws(() =>
    parse({ outcome: "no_matches", failure_reason: null, notices: [notice] }),
  );
});
test("a title and returned schema fields are required", () => {
  assert.throws(() =>
    parse({
      outcome: "success",
      failure_reason: null,
      notices: [{ ...notice, title: "" }],
    }),
  );
});
test("all returned document URLs must use the exact allowed HTTPS source hosts", () => {
  for (const url of [
    "http://iiitd.ac.in/test.pdf",
    "https://iiitd.ac.in.evil.test/test.pdf",
    "https://127.0.0.1/test.pdf",
    "https://user:pass@iiitd.ac.in/test.pdf",
    "https://iiitd.ac.in:8443/test.pdf",
  ])
    assert.throws(() => validateSourceUrl(url));
  assert.throws(() =>
    parse({
      outcome: "success",
      failure_reason: null,
      notices: [
        { ...notice, amendment_urls: ["https://example.com/amendment.pdf"] },
      ],
    }),
  );
});
test("duplicate notices and over-limit batches are rejected", () => {
  assert.throws(
    () =>
      parse({
        outcome: "success",
        failure_reason: null,
        notices: [notice, notice],
      }),
    /duplicate/,
  );
  assert.throws(
    () =>
      parse({
        outcome: "success",
        failure_reason: null,
        notices: Array(6).fill(notice),
      }),
    /at most five/,
  );
});

test("notice identity survives a new run and a changed listing order", () => {
  const first = { ...notice, notice_id: "GEM/2026/B/8183492" };
  const second = { ...notice, notice_id: "GEM/2026/B/8106278" };
  const previous = validateDiscoveryResult(
    { outcome: "success", failure_reason: null, notices: [first, second] },
    "2026-10-24T09:00:00Z",
    "run-one",
  );
  const next = validateDiscoveryResult(
    { outcome: "success", failure_reason: null, notices: [second, first] },
    "2026-10-25T09:00:00Z",
    "run-two",
  );
  assert.equal(previous[0].id, next[1].id);
  assert.equal(previous[1].id, next[0].id);
  assert.notEqual(previous[0].sourceRunId, next[1].sourceRunId);
});

test("bundled TinyFish snapshot supplies real source records without eligibility claims", () => {
  const snapshot = JSON.parse(
    readFileSync(new URL("./data/iiitd-tenders.json", import.meta.url), "utf8"),
  );
  assert.equal(snapshot.provider, "TinyFish");
  assert.match(snapshot.providerRunId, /^[a-f0-9-]{36}$/);
  const tenders = validateDiscoveryResult(
    snapshot.result,
    snapshot.retrievedAt,
    snapshot.providerRunId,
  );
  assert.ok(tenders.length > 0);
  for (const tender of tenders) {
    assert.equal(tender.provenance, "live");
    assert.ok(tender.pdfUrls.length > 0);
    assert.deepEqual(tender.conditions, []);
    assert.equal(tender.value, "Not extracted");
  }
});
