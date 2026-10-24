import assert from "node:assert/strict";
import test from "node:test";
import { hasVerifiedDocument } from "./certificate-verification.ts";
import type { CertificateVerification } from "./certificate-types";

const profile = {
  company: "Example Supplies Private Limited",
  contact: "Example Person",
};
const now = new Date("2026-10-24T12:00:00Z");
const verified: CertificateVerification = {
  id: "receipt-1",
  kind: "gst",
  provider: "entitylocker",
  environment: "live",
  subjectName: profile.company,
  maskedNumber: "•••••••••••1Z5",
  status: "verified",
  issuer: "Goods and Services Tax Network",
  message: "Issuer verified",
  createdAt: "2026-10-24T10:00:00Z",
  verifiedAt: "2026-10-24T11:00:00Z",
  validUntil: "2026-10-25T11:00:00Z",
};

test("only a live, current issuer receipt matching the profile can display a badge", () => {
  assert.equal(hasVerifiedDocument(verified, profile, now), true);
  assert.equal(
    hasVerifiedDocument(
      verified,
      { ...profile, company: "Another Company" },
      now,
    ),
    false,
  );
  assert.equal(
    hasVerifiedDocument(
      { ...verified, validUntil: now.toISOString() },
      profile,
      now,
    ),
    false,
  );
  assert.equal(
    hasVerifiedDocument({ ...verified, validUntil: null }, profile, now),
    false,
  );
  assert.equal(
    hasVerifiedDocument(
      { ...verified, verifiedAt: "2026-10-26T11:00:00Z" },
      profile,
      now,
    ),
    false,
  );
});

test("test-mode and incomplete provider sessions can never award the live badge", () => {
  for (const status of [
    "test_passed",
    "pending",
    "submission_unknown",
    "failed",
    "review",
    "expired",
  ] as const)
    assert.equal(
      hasVerifiedDocument({ ...verified, status }, profile, now),
      false,
    );
  assert.equal(
    hasVerifiedDocument({ ...verified, environment: "test" }, profile, now),
    false,
  );
  assert.equal(
    hasVerifiedDocument({ ...verified, provider: "digilocker" }, profile, now),
    false,
  );
});

test("a personal PAN receipt cannot verify a business GST certificate", () => {
  const pan = {
    ...verified,
    kind: "pan" as const,
    provider: "digilocker" as const,
    subjectName: profile.contact,
  };
  assert.equal(hasVerifiedDocument(pan, profile, now), true);
  assert.equal(
    hasVerifiedDocument({ ...pan, subjectName: profile.company }, profile, now),
    false,
  );
});
