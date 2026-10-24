"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { downloadDemoReceipt, formatDemoAmount } from "@/lib/purchases";
import type { DemoPurchase } from "@/lib/purchases";
import { Icon } from "./icon";
import { useWorkspace } from "./workspace-provider";

export function identityLabel(status: DemoPurchase["identityStatus"]) {
  return status === "verified"
    ? "DigiLocker verified"
    : status === "test_passed"
      ? "DigiLocker test check passed"
      : "Identity unverified · demo only";
}

export function PurchaseReceipt({ order }: { order: DemoPurchase }) {
  return (
    <section className="purchase-receipt" aria-label="Demo purchase receipt">
      <span className="status-badge status-meets">
        <Icon name="checkCircle" size={15} />
        Demo purchased
      </span>
      <h3>Your demo purchase is complete.</h3>
      <p>
        No money was charged. Your receipt is saved to your supplier account.
      </p>
      <dl className="checkout-summary">
        <div>
          <dt>Receipt</dt>
          <dd>{order.receiptNumber}</dd>
        </div>
        <div>
          <dt>Supplier</dt>
          <dd>{order.supplier.company}</dd>
        </div>
        <div>
          <dt>Demo amount</dt>
          <dd>{formatDemoAmount(order.amountPaise)}</dd>
        </div>
        <div>
          <dt>Actually charged</dt>
          <dd>₹0</dd>
        </div>
        <div>
          <dt>Identity at checkout</dt>
          <dd>{identityLabel(order.identityStatus)}</dd>
        </div>
        <div>
          <dt>Completed</dt>
          <dd>
            {order.purchasedAt
              ? `${new Date(order.purchasedAt).toLocaleString("en-GB", { timeZone: "Asia/Kolkata" })} IST`
              : "—"}
          </dd>
        </div>
      </dl>
      <p className="review-source-note">
        This receipt records a hackathon simulation. It is not an issuer
        receipt, bid submission, reservation or contract award. The official
        documents remain publicly available.
      </p>
      <div className="purchase-actions">
        <button
          className="button button-primary button-small"
          onClick={() => downloadDemoReceipt(order)}
        >
          <Icon name="download" size={16} />
          Download demo receipt
        </button>
        <a
          className="button button-secondary button-small"
          href={order.tender.pdfUrls[0] ?? order.tender.sourceUrl}
          target="_blank"
          rel="noreferrer"
        >
          Open official documents <Icon name="arrow" size={15} />
        </a>
      </div>
    </section>
  );
}

export function DemoCheckout({
  initialOrder,
  onBack,
}: {
  initialOrder: DemoPurchase;
  onBack: () => void;
}) {
  const { purchaseFlow } = useWorkspace();
  const [order, setOrder] = useState(initialOrder);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    heading.current?.focus();
  }, []);
  async function pay(outcome: "success" | "failure") {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      setOrder(await purchaseFlow.pay(order.id, outcome));
    } catch (failure) {
      setError(
        failure instanceof Error
          ? failure.message
          : "Could not confirm the demo payment. Please retry.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="drawer-body tender-review-body">
      <button className="text-link" onClick={onBack} disabled={busy}>
        ← Back to tender review
      </button>
      <h3 ref={heading} tabIndex={-1}>
        {order.status === "purchased"
          ? "Demo receipt"
          : "Complete your demo checkout"}
      </h3>
      {order.status === "purchased" ? (
        <>
          <PurchaseReceipt order={order} />
          <Link className="button button-secondary" href="/dashboard/purchases">
            Go to My tenders <Icon name="arrowRight" size={16} />
          </Link>
        </>
      ) : (
        <section className="checkout-card">
          <span className="subtle-tag">SIMULATED PAYMENT · NO REAL CHARGE</span>
          <dl className="checkout-summary">
            <div>
              <dt>Business</dt>
              <dd>{order.supplier.company}</dd>
            </div>
            <div>
              <dt>Contact</dt>
              <dd>{order.supplier.email}</dd>
            </div>
            <div>
              <dt>DigiLocker identity</dt>
              <dd>{identityLabel(order.identityStatus)}</dd>
            </div>
            <div>
              <dt>Demo tender amount</dt>
              <dd>{formatDemoAmount(order.amountPaise)}</dd>
            </div>
            <div>
              <dt>Total charged</dt>
              <dd>₹0 · simulation only</dd>
            </div>
          </dl>
          <p>
            No card, UPI details or banking information are needed. Choose an
            outcome to try the purchase flow.
          </p>
          {order.status === "failed" && (
            <div className="inline-notice" role="alert">
              The simulated payment failed. Nothing was charged. Retry below
              using the same order.
            </div>
          )}
          {error && (
            <div className="error-banner" role="alert">
              {error}
            </div>
          )}
          <div className="purchase-actions">
            <button
              className="button button-primary"
              disabled={busy}
              aria-busy={busy}
              onClick={() => void pay("success")}
            >
              <Icon
                name={busy ? "refresh" : "checkCircle"}
                size={17}
                className={busy ? "spin" : ""}
              />
              {busy
                ? "Confirming demo payment…"
                : order.status === "failed"
                  ? "Retry demo payment — success"
                  : "Simulate successful payment"}
            </button>
            <button
              className="button button-secondary"
              disabled={busy}
              onClick={() => void pay("failure")}
            >
              Simulate failed payment
            </button>
          </div>
          <p className="review-source-note">
            The displayed ₹499 is for the hackathon demo. Check the official
            notice for actual fees and submission steps.
          </p>
        </section>
      )}
    </div>
  );
}
