import assert from "node:assert/strict";
import { test } from "node:test";
import { parseIiitdDeadline } from "./source-deadline.ts";

test("IIIT-Delhi English deadlines use campus time, including noon and midnight", () => {
  assert.equal(
    parseIiitdDeadline("11th November 2026 at 3:00 PM"),
    "2026-11-11T15:00:00+05:30",
  );
  assert.equal(
    parseIiitdDeadline("6th Nov 2026 at 3:00 PM"),
    "2026-11-06T15:00:00+05:30",
  );
  assert.equal(
    parseIiitdDeadline("21st Oct 2026 at 12:00 Noon"),
    "2026-10-21T12:00:00+05:30",
  );
  assert.equal(
    parseIiitdDeadline("21st Oct 2026 at 12:00 AM"),
    "2026-10-21T00:00:00+05:30",
  );
});

test("ambiguous, missing and impossible deadlines stay unresolved", () => {
  for (const value of [
    null,
    "",
    "6 November 2026",
    "31st Feb 2026 at 3:00 PM",
    "6th Nov 2026 at 25:00 PM",
    "6th Nov 2026 at 3:90 PM",
    "6th Nov 2026 at 1:00 Noon",
    "6th Nov 2026 at 3:00 PM UTC",
  ])
    assert.equal(parseIiitdDeadline(value), null);
});
