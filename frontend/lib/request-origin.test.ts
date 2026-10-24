import assert from "node:assert/strict";
import { test } from "node:test";
import { isWorkspaceOrigin } from "./request-origin.ts";

test("HTTPS mutations behind a private proxy match the configured public origin", () => {
  const request = new Request("http://web:3000/api/profile", {
    headers: {
      Origin: "https://demo.example",
      "X-Forwarded-Host": "attacker.example",
    },
  });
  assert.equal(isWorkspaceOrigin(request, "https://demo.example"), true);
  assert.equal(isWorkspaceOrigin(request, "https://other.example"), false);
});

test("untrusted origins and forwarded headers cannot authorize a mutation", () => {
  const request = new Request("http://web:3000/api/purchases", {
    headers: {
      Origin: "https://demo.example.evil.test",
      "X-Forwarded-Host": "demo.example",
      "X-Forwarded-Proto": "https",
    },
  });
  assert.equal(isWorkspaceOrigin(request, "https://demo.example"), false);
  assert.equal(isWorkspaceOrigin(request, "invalid configuration"), false);
  assert.equal(
    isWorkspaceOrigin(
      new Request("http://localhost:3000/api/profile", {
        headers: { Origin: "http://localhost:3000" },
      }),
      "",
    ),
    true,
  );
});
