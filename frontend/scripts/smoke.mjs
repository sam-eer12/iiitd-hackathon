import assert from "node:assert/strict";

const base = process.env.SMOKE_BASE_URL ?? "http://127.0.0.1:3000";
const pages = [
  ["/", "Find the tender"],
  ["/dashboard", "Your tender shortlist"],
  ["/dashboard/tenders", "Find your next good fit."],
  ["/dashboard/saved", "Your saved shortlist"],
  ["/dashboard/profile", "Your business, in focus."],
  ["/dashboard/sources", "IIIT-Delhi"],
  ["/dashboard/amendments", "No amendment links in this discovery."],
  ["/dashboard/settings", "Your workspace, your way."],
  ["/dashboard/help", "Find your feet."],
  ["/architecture", "From opportunity"],
  ["/samples/sample-1", "Illustrative sample document"],
  ["/architecture.mmd", "flowchart TB"],
];

for (const [route, expected] of pages) {
  const response = await fetch(`${base}${route}`);
  assert.equal(response.status, 200, route);
  assert.ok(
    (await response.text()).includes(expected),
    `${route}: content missing`,
  );
  console.log(`${route}: 200, expected content present`);
}
const configurationResponse = await fetch(`${base}/api/discovery`);
assert.equal(configurationResponse.status, 200);
const configuration = await configurationResponse.json();
assert.equal(typeof configuration.configured, "boolean");
assert.equal(typeof configuration.tokenRequired, "boolean");
console.log("Discovery configuration:", configuration);

const catalogResponse = await fetch(`${base}/api/tenders`);
assert.equal(catalogResponse.status, 200);
const catalog = await catalogResponse.json();
assert.ok(Array.isArray(catalog.tenders));
assert.ok(Number.isFinite(Date.parse(catalog.retrievedAt)));
for (const tender of catalog.tenders) {
  assert.equal(tender.provenance, "live");
  assert.equal(new URL(tender.sourceUrl).hostname, "iiitd.ac.in");
  assert.deepEqual(tender.conditions, []);
}
console.log(`Public source catalog: ${catalog.tenders.length} real notices`);

const crossOrigin = await fetch(`${base}/api/discovery`, {
  method: "POST",
  headers: {
    Origin: "https://untrusted.example",
    "Content-Type": "application/json",
  },
  body: "{}",
});
assert.equal(crossOrigin.status, 403);
console.log("Cross-origin submission: rejected (403)");
const unsigned = await fetch(
  `${base}/api/discovery/00000000-0000-0000-0000-000000000000`,
);
assert.equal(unsigned.status, 403);
console.log("Unsigned job lookup: rejected (403)");
const missing = await fetch(`${base}/samples/not-a-notice`);
const missingBody = await missing.text();
assert.ok([200, 404].includes(missing.status));
assert.match(missingBody, /This page could not be found/);
assert.match(missingBody, /<meta\s+name="robots"\s+content="noindex"\s*\/?>/);
assert.ok(!missingBody.includes('class="sample-paper"'));
console.log(
  `Unknown sample document: not-found content and noindex (HTTP ${missing.status})`,
);
console.log("Smoke checks passed. No metered TinyFish run was started.");
