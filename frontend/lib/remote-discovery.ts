import "server-only";
import { backendFetch, proxyBackend } from "./backend-proxy";
import { INITIAL_TENDER_CATALOG } from "./tender-catalog";
import { validateDiscoveryResult } from "./discovery-validation";
import type { DiscoveryJob } from "./types";

export async function remoteCatalog() {
  const response = await backendFetch("catalog");
  if (!response.ok) throw new Error("Source catalog unavailable");
  const result = await response.json();
  if (
    !result.payload ||
    Date.parse(result.observedAt) <=
      Date.parse(INITIAL_TENDER_CATALOG.retrievedAt)
  )
    return INITIAL_TENDER_CATALOG;
  return {
    ...INITIAL_TENDER_CATALOG,
    tenders: validateDiscoveryResult(
      result.payload,
      result.observedAt,
      result.providerRunId ?? "",
    ),
    retrievedAt: result.observedAt,
    providerRunId: result.providerRunId ?? "",
  };
}

export async function remoteDiscovery(request: Request, id?: string) {
  const origin = request.headers.get("origin");
  if (
    request.method !== "GET" &&
    origin &&
    origin !== new URL(request.url).origin
  )
    return Response.json(
      { error: "Use this workspace to start source collection." },
      { status: 403 },
    );
  if (id && !request.headers.get("authorization")?.startsWith("Bearer "))
    return Response.json(
      { error: "Sign in to access your source run." },
      { status: 403 },
    );

  if (!id && request.method === "GET") {
    try {
      const response = await backendFetch("catalog/configuration");
      return Response.json(await response.json(), {
        status: response.status,
        headers: { "Cache-Control": "no-store" },
      });
    } catch {
      return Response.json({ configured: false, tokenRequired: false });
    }
  }
  if (id && !/^[a-f0-9-]{36}$/i.test(id))
    return Response.json({ error: "Invalid source run." }, { status: 400 });
  const forwarded = id
    ? request
    : new Request(request.url, {
        method: "POST",
        headers: {
          ...Object.fromEntries(request.headers),
          "Idempotency-Key":
            request.headers.get("idempotency-key") ?? crypto.randomUUID(),
        },
        body: JSON.stringify({ sourceId: "iiitd", mode: "discovery" }),
      });
  const response = await proxyBackend(
    forwarded,
    id ? `refreshes/${id}` : "refreshes",
  );
  const payload = await response.json();
  if (!response.ok)
    return Response.json(
      { error: payload.error?.message ?? "Could not access this source run." },
      { status: response.status },
    );
  const value = payload.job;
  const job: DiscoveryJob = {
    id: value.id,
    providerRunId: value.providerRunId,
    status: value.status === "queued" ? "running" : value.status,
    createdAt: value.createdAt,
    finishedAt: value.finishedAt ?? undefined,
    error: value.errorMessage ?? undefined,
  };
  if (job.status === "completed") {
    try {
      job.tenders = (await remoteCatalog()).tenders;
    } catch {
      return Response.json(
        { error: "The completed source snapshot is temporarily unavailable." },
        { status: 503 },
      );
    }
  }
  return Response.json(
    { job },
    { status: response.status, headers: { "Cache-Control": "no-store" } },
  );
}
