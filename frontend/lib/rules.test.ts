import assert from "node:assert/strict";
import { test } from "node:test";
import { evaluateCondition, evaluateTender } from "./rules.ts";
import type { Condition, SupplierProfile, Tender } from "./types.ts";

const profile: SupplierProfile = {
  company: "Test Supplier",
  contact: "Test",
  email: "test@example.com",
  categories: ["Electronics"],
  turnover: [
    { year: "2023–24", amount: 3000000 },
    { year: "2024–25", amount: 3500000 },
    { year: "2025–26", amount: 4000000 },
  ],
  completedOrders: 3,
  depositCapacity: 50000,
  certificates: { gst: true, iso: false, manufacturer: null },
};
const now = new Date("2026-10-24T09:00:00+05:30");
const evidence = {
  quote: "An explicitly evidenced sample requirement.",
  page: 4,
  clause: "3.2",
};
const turnover: Condition = {
  ...evidence,
  type: "turnover",
  label: "Turnover",
  requirement: "Average at least 35 lakh",
  years: ["2023–24", "2024–25", "2025–26"],
  threshold: 3500000,
};
const tender: Tender = {
  id: "test",
  reference: "TEST",
  title: "Test",
  description: "",
  issuer: "Test",
  category: "Electronics",
  value: "",
  deadlineText: null,
  deadline: null,
  relevance: null,
  sourceUrl: "https://iiitd.ac.in/tenders",
  pdfUrls: [],
  amendmentUrls: [],
  provenance: "sample",
  retrievedAt: now.toISOString(),
  amended: false,
  conditions: [],
};

test("exact required years support an average at the threshold", () => {
  assert.equal(evaluateCondition(turnover, profile, now).status, "meets");
});
test("a missing financial year cannot silently pass", () => {
  assert.equal(
    evaluateCondition(
      turnover,
      { ...profile, turnover: profile.turnover.slice(1) },
      now,
    ).status,
    "review",
  );
});
test("zero is a known amount and blocks a positive threshold", () => {
  assert.equal(
    evaluateCondition(
      {
        ...evidence,
        type: "deposit",
        label: "EMD",
        requirement: "₹1",
        threshold: 1,
      },
      { ...profile, depositCapacity: 0 },
      now,
    ).status,
    "blocked",
  );
});
test("unknown and explicitly absent certificates have different results", () => {
  const certificate: Condition = {
    ...evidence,
    type: "certificate",
    label: "Certificate",
    requirement: "OEM",
    certificate: "manufacturer",
  };
  assert.equal(evaluateCondition(certificate, profile, now).status, "review");
  assert.equal(
    evaluateCondition({ ...certificate, certificate: "iso" }, profile, now)
      .status,
    "blocked",
  );
});
test("missing evidence prevents a pass", () => {
  assert.equal(
    evaluateCondition({ ...turnover, quote: "" }, profile, now).status,
    "review",
  );
});
test("an exact passed deadline blocks, including equality", () => {
  assert.equal(
    evaluateCondition(
      {
        ...evidence,
        type: "deadline",
        label: "Deadline",
        requirement: "Now",
        deadline: now.toISOString(),
      },
      profile,
      now,
    ).status,
    "blocked",
  );
});
test("a date-only deadline stays unresolved", () => {
  assert.equal(
    evaluateCondition(
      {
        ...evidence,
        type: "deadline",
        label: "Deadline",
        requirement: "Date only",
        deadline: "2026-11-01",
      },
      profile,
      now,
    ).status,
    "review",
  );
});
test("no clauses and incomplete clause groups cannot pass", () => {
  assert.equal(evaluateTender(tender, profile, now).status, "review");
  assert.equal(
    evaluateTender({ ...tender, conditions: [turnover] }, profile, now).status,
    "review",
  );
});
test("a known blocker takes precedence while preserving unresolved findings", () => {
  const result = evaluateTender(
    {
      ...tender,
      conditions: [
        { ...turnover, threshold: 5000000 },
        {
          ...evidence,
          type: "certificate",
          label: "OEM",
          requirement: "OEM",
          certificate: "manufacturer",
        },
      ],
    },
    profile,
    now,
  );
  assert.equal(result.status, "blocked");
  assert.equal(result.findings[1].status, "review");
});
test("all five supported, evidenced checks must pass for aggregate Meets", () => {
  const conditions: Condition[] = [
    turnover,
    {
      ...evidence,
      type: "experience",
      label: "Experience",
      requirement: "3 orders",
      threshold: 3,
    },
    {
      ...evidence,
      type: "certificate",
      label: "GST",
      requirement: "GST",
      certificate: "gst",
    },
    {
      ...evidence,
      type: "deposit",
      label: "EMD",
      requirement: "₹50,000",
      threshold: 50000,
    },
    {
      ...evidence,
      type: "deadline",
      label: "Deadline",
      requirement: "Later",
      deadline: "2026-11-06T15:00:00+05:30",
    },
  ];
  assert.equal(
    evaluateTender({ ...tender, conditions }, profile, now).status,
    "meets",
  );
});
