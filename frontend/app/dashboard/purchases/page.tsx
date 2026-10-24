"use client";

import Link from "next/link";
import { useState } from "react";
import { PurchaseReceipt } from "@/components/demo-checkout";
import { Icon } from "@/components/icon";
import { TenderDrawer } from "@/components/tender-drawer";
import { useWorkspace } from "@/components/workspace-provider";
import { useAuth } from "@/lib/auth-context";
import { sourceReviewVersion, tenderAvailability } from "@/lib/purchases";

export default function PurchasesPage() {
  const { user, loading: authLoading, signInWithGoogle } = useAuth();
  const { purchaseFlow, tenders, evaluationTime } = useWorkspace();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [signInError, setSignInError] = useState("");
  const [signingIn, setSigningIn] = useState(false);
  const selected = tenders.find((tender) => tender.id === selectedId);
  return (
    <>
      <div className="workspace-heading">
        <div>
          <div className="eyebrow">YOUR DEMO PURCHASES</div>
          <h1>My tenders.</h1>
          <p>
            Resume a demo checkout, find your receipts and return to the
            official documents.
          </p>
        </div>
        <Link
          className="button button-primary button-small"
          href="/dashboard/tenders"
        >
          Find a tender <Icon name="arrowRight" size={16} />
        </Link>
      </div>
      {authLoading || purchaseFlow.loading ? (
        <div className="loading-panel">Loading your demo purchases…</div>
      ) : !user ? (
        <section className="checkout-card purchase-signin">
          <Icon name="building" size={28} />
          <h2>Your tenders belong to your account.</h2>
          <p>
            Sign in with Google to view and save your demo purchases across
            devices.
          </p>
          <button
            className="button button-primary"
            disabled={signingIn}
            onClick={async () => {
              setSigningIn(true);
              setSignInError("");
              try {
                await signInWithGoogle();
              } catch {
                setSignInError(
                  "Google sign-in did not finish. Please try again.",
                );
              } finally {
                setSigningIn(false);
              }
            }}
          >
            {signingIn ? "Signing in…" : "Sign in with Google"}
          </button>
          {signInError && <p role="alert">{signInError}</p>}
        </section>
      ) : (
        <>
          {purchaseFlow.error && (
            <div className="error-banner" role="alert">
              <span>{purchaseFlow.error}</span>
              <button
                className="text-link"
                onClick={() => void purchaseFlow.reload()}
              >
                Retry loading purchases
              </button>
            </div>
          )}
          {!purchaseFlow.error && !purchaseFlow.orders.length && (
            <div className="empty-state">
              <Icon name="document" size={32} />
              <h2>No demo purchases yet.</h2>
              <p>
                Find an open tender, review its documents and complete the demo
                checkout.
              </p>
              <Link
                className="button button-primary button-small"
                href="/dashboard/tenders"
              >
                Discover tenders <Icon name="arrowRight" size={16} />
              </Link>
            </div>
          )}
          <div className="purchase-list">
            {purchaseFlow.orders.map((order) => {
              const current = tenders.find(
                (tender) => tender.id === order.tender.id,
              );
              const canResume =
                current &&
                tenderAvailability(current, new Date(evaluationTime)) ===
                  "open";
              return (
                <article key={order.id}>
                  <span
                    className={`status-badge status-${order.status === "purchased" ? "meets" : "review"}`}
                  >
                    {order.status === "purchased"
                      ? "Demo purchased"
                      : order.status === "failed"
                        ? "Demo payment failed"
                        : "Checkout started"}
                  </span>
                  <h2>{order.tender.title}</h2>
                  <p className="muted">
                    {order.tender.issuer} · {order.tender.reference}
                  </p>
                  {order.status === "purchased" ? (
                    <PurchaseReceipt order={order} />
                  ) : (
                    <>
                      <p className="review-source-note">
                        {canResume
                          ? "Review the current notice before resuming this demo checkout. Nothing has been charged."
                          : "This notice is no longer open in the current catalog. Its documents are still available."}
                      </p>
                      <div className="purchase-actions">
                        {canResume && (
                          <button
                            className="button button-primary button-small"
                            onClick={() => setSelectedId(order.tender.id)}
                          >
                            Review & resume <Icon name="arrowRight" size={15} />
                          </button>
                        )}
                        <a
                          className="button button-secondary button-small"
                          href={
                            order.tender.pdfUrls[0] ?? order.tender.sourceUrl
                          }
                          target="_blank"
                          rel="noreferrer"
                        >
                          Official documents <Icon name="arrow" size={15} />
                        </a>
                      </div>
                    </>
                  )}
                </article>
              );
            })}
          </div>
        </>
      )}
      {selected && (
        <TenderDrawer
          key={sourceReviewVersion(selected)}
          tender={selected}
          onClose={() => setSelectedId(null)}
        />
      )}
    </>
  );
}
