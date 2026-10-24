import assert from "node:assert/strict";
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
