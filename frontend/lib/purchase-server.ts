import "server-only";
import { isWorkspaceOrigin } from "./request-origin";
import { backendFetch, proxyBackend, remoteWorkspace } from "./backend-proxy";
import { latestTenderCatalog } from "./discovery-server";
import { remoteCatalog } from "./remote-discovery";
import {
  purchaseSnapshot,
  sourceReviewVersion,
  tenderAvailability,
} from "./purchases";
import type { DemoPurchase } from "./purchases";

const headers = { "Cache-Control": "no-store" };
const errorResponse = (message: string, status: number) =>
  Response.json({ error: { message } }, { status, headers });

function validateRequest(request: Request) {
  if (!request.headers.get("authorization")?.startsWith("Bearer "))
    return errorResponse("Sign in with Google to continue to checkout.", 401);
  if (!isWorkspaceOrigin(request))
    return errorResponse("Use this workspace to complete checkout.", 403);
}

async function catalog() {
  return remoteWorkspace() ? remoteCatalog() : latestTenderCatalog();
}

export async function startPurchase(request: Request) {
  const invalid = validateRequest(request);
  if (invalid) return invalid;
  try {
    const raw = await request.text();
    if (Buffer.byteLength(raw) > 32768)
      return errorResponse("Checkout request is too large.", 413);
    let body;
    try {
      body = JSON.parse(raw);
    } catch {
      return errorResponse("Invalid checkout request.", 400);
    }
    if (
      !body ||
      typeof body.tenderId !== "string" ||
      body.reviewed !== true ||
      body.demoAcknowledged !== true
    )
      return errorResponse(
        "Review the documents and acknowledge the demo checkout first.",
        422,
      );
    const tender = (await catalog()).tenders.find(
      (item) => item.id === body.tenderId,
    );
    if (!tender)
      return errorResponse(
        "This notice is no longer in the current catalog. Refresh tenders.",
        404,
      );
    if (body.reviewVersion !== sourceReviewVersion(tender))
      return errorResponse(
        "The notice changed. Close this panel and review the latest tender before checkout.",
        409,
      );
    if (tenderAvailability(tender, new Date()) !== "open")
      return errorResponse(
        "This tender is closed or its deadline is unconfirmed. Its documents are still available for review.",
        409,
      );
    // Never forward client-supplied titles, links, prices, receipts or statuses.
    return proxyBackend(
      new Request(request.url, {
        method: "POST",
        headers: request.headers,
        body: JSON.stringify({
          tender: purchaseSnapshot(tender),
          reviewed: true,
          demoAcknowledged: true,
        }),
      }),
      "demo-purchases",
    );
  } catch {
    return errorResponse(
      "Checkout is unavailable. No payment was made. Please try again.",
      503,
    );
  }
}

export async function payPurchase(request: Request, id: string) {
  const invalid = validateRequest(request);
  if (invalid) return invalid;
  if (!/^[a-f0-9-]{36}$/i.test(id))
    return errorResponse("Invalid demo order.", 400);
  try {
    const existing = await backendFetch(`demo-purchases/${id}`, {
      headers: { Authorization: request.headers.get("authorization")! },
    });
    const order: DemoPurchase = await existing.json();
    if (!existing.ok)
      return Response.json(order, { status: existing.status, headers });
    // A retry after a lost response always returns the original receipt.
    if (order.status === "purchased") return Response.json(order, { headers });
    const tender = (await catalog()).tenders.find(
      (item) => item.id === order.tender.id,
    );
    if (
      !tender ||
      sourceReviewVersion(tender) !== sourceReviewVersion(order.tender)
    )
      return errorResponse(
        "The notice changed. Close checkout and review the latest tender before trying again.",
        409,
      );
    return proxyBackend(request, `demo-purchases/${id}/pay`);
  } catch {
    return errorResponse(
      "Could not confirm the demo payment. Retry to recover this order's status.",
      503,
    );
  }
}
