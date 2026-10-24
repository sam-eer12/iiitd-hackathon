import assert from "node:assert/strict";
import { test } from "node:test";
import { DEFAULT_PROFILE } from "./demo-data.ts";
import { validateDiscoveryResult } from "./discovery-validation.ts";
import { restoreWorkspace, type StoredWorkspace } from "./workspace-storage.ts";

const tenders = validateDiscoveryResult(
  {
    outcome: "success",
    failure_reason: null,
    notices: [
      {
        notice_id: "source-ref",
        title: "Source notice",
        source_url: "https://iiitd.ac.in/tenders",
        deadline_text: null,
        pdf_urls: [],
        amendment_urls: [],
      },
    ],
  },
  "2026-10-24T12:00:00Z",
  "recorded-run",
);
const initial: StoredWorkspace = {
  profile: DEFAULT_PROFILE,
  liveTenders: tenders,
  savedIds: [],
  job: null,
  collapsed: false,
  catalogRetrievedAt: "2026-10-24T12:00:00Z",
};

test("a saved sample workspace migrates to real notices and keeps the supplier profile", () => {
  const profile = { ...DEFAULT_PROFILE, company: "Saved business" };
  const restored = restoreWorkspace(
    {
      profile,
      liveTenders: [],
      savedIds: ["sample-1"],
      collectionMode: "sample",
      collapsed: true,
    },
    initial,
  );
  assert.equal(restored.profile.company, "Saved business");
  assert.deepEqual(restored.liveTenders, tenders);
  assert.deepEqual(restored.savedIds, []);
  assert.equal(restored.collapsed, true);
});

test("legacy live bookmarks migrate to source identity across new runs", () => {
  const legacy = {
    ...tenders[0],
    id: "live-old-run-0",
    retrievedAt: "2026-10-25T12:00:00Z",
  };
  const restored = restoreWorkspace(
    {
      ...initial,
      liveTenders: [legacy],
      savedIds: [legacy.id],
      catalogRetrievedAt: legacy.retrievedAt,
    },
    initial,
  );
  assert.equal(restored.liveTenders[0].id, tenders[0].id);
  assert.deepEqual(restored.savedIds, [tenders[0].id]);
});

test("a newer no-matches result stays empty and never falls back to synthetic tenders", () => {
  const restored = restoreWorkspace(
    { ...initial, liveTenders: [], catalogRetrievedAt: "2026-10-25T12:00:00Z" },
    initial,
  );
  assert.deepEqual(restored.liveTenders, []);
});

test("cached source data on an unapproved host is discarded", () => {
  const restored = restoreWorkspace(
    {
      ...initial,
      liveTenders: [{ ...tenders[0], sourceUrl: "https://untrusted.example" }],
      catalogRetrievedAt: "2026-10-25T12:00:00Z",
    },
    initial,
  );
  assert.deepEqual(restored, initial);
});
