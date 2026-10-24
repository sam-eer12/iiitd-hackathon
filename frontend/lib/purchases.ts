import type { Tender } from "./types";

export type PurchaseTender = Pick<
  Tender,
  | "id"
  | "reference"
  | "title"
  | "issuer"
  | "sourceUrl"
  | "pdfUrls"
  | "amendmentUrls"
  | "deadline"
  | "deadlineText"
  | "retrievedAt"
>;

export interface DemoPurchase {
  id: string;
  tender: PurchaseTender;
  supplier: { company: string; contact: string; email: string };
  amountPaise: number;
  currency: "INR";
  status: "pending" | "failed" | "purchased";
  identityStatus: "verified" | "test_passed" | "unverified";
  createdAt: string;
  updatedAt: string;
  purchasedAt: string | null;
  demo: true;
  receiptNumber: string | null;
}

export function tenderAvailability(
  tender: Pick<Tender, "deadline">,
  now: Date,
): "open" | "closed" | "unknown" {
  const deadline = Date.parse(tender.deadline ?? "");
  if (!Number.isFinite(deadline)) return "unknown";
  return deadline > now.getTime() ? "open" : "closed";
}

// Bind the review acknowledgement to the exact notice the supplier saw.
// Collection time alone changing does not invalidate a review.
export function sourceReviewVersion(tender: PurchaseTender): string {
  return JSON.stringify([
    tender.id,
    tender.title,
    tender.reference,
    tender.sourceUrl,
    tender.deadline,
    tender.deadlineText,
    [...tender.pdfUrls].sort(),
    [...tender.amendmentUrls].sort(),
  ]);
}

export function purchaseSnapshot(tender: Tender): PurchaseTender {
  const {
    id,
    reference,
    title,
    issuer,
    sourceUrl,
    pdfUrls,
    amendmentUrls,
    deadline,
    deadlineText,
    retrievedAt,
  } = tender;
  return {
    id,
    reference,
    title,
    issuer,
    sourceUrl,
    pdfUrls,
    amendmentUrls,
    deadline,
    deadlineText,
    retrievedAt,
  };
}

export function formatDemoAmount(amountPaise: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amountPaise / 100);
}

export function downloadDemoReceipt(order: DemoPurchase) {
  if (order.status !== "purchased" || !order.receiptNumber) return;
  const receipt = {
    title: "TenderLens hackathon demo receipt - no real payment",
    ...order,
    amountChargedPaise: 0,
    notice:
      "Simulated purchase only. The demo amount is not the issuer's tender fee. No bid, reservation or contract award was made. Official documents remain publicly available.",
  };
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(receipt, null, 2)], { type: "application/json" }),
  );
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${order.receiptNumber}.json`;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
