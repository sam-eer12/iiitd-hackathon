"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { hasVerifiedDocument } from "@/lib/certificate-verification";
import { tenderAvailability } from "@/lib/purchases";
import type { DemoPurchase } from "@/lib/purchases";
import type { Tender } from "@/lib/types";
import { DemoCheckout } from "./demo-checkout";
import { Icon } from "./icon";
import { useWorkspace } from "./workspace-provider";

export function AvailabilityBadge({
  status,
}: {
  status: "open" | "closed" | "unknown";
}) {
  return (
    <span
      className={`status-badge status-${status === "open" ? "meets" : status === "closed" ? "blocked" : "review"}`}
    >
      <Icon
        name={
          status === "open" ? "clock" : status === "closed" ? "close" : "alert"
        }
        size={13}
      />
      {status === "open"
        ? "Open"
        : status === "closed"
          ? "Closed"
          : "Deadline unconfirmed"}
    </span>
  );
}

export function TenderDrawer({
  tender,
  onClose,
}: {
  tender: Tender;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const { user, signInWithGoogle } = useAuth();
  const {
    profile,
    savedIds,
    toggleSaved,
    evaluationTime,
    certificateVerification,
    purchaseFlow,
  } = useWorkspace();
  const [reviewed, setReviewed] = useState(false);
  const [demoAcknowledged, setDemoAcknowledged] = useState(false);
  const [order, setOrder] = useState<DemoPurchase | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const availability = tenderAvailability(tender, new Date(evaluationTime));
  const existing = purchaseFlow.orders.find(
    (item) => item.tender.id === tender.id,
  );
  const profileComplete = Boolean(
    profile.company.trim() &&
    profile.contact.trim() &&
    profile.email.includes("@") &&
    profile.categories.length,
  );
  const identityVerified = certificateVerification.records.some(
    (record) =>
      record.kind === "pan" &&
      hasVerifiedDocument(record, profile, new Date(evaluationTime)),
  );

  useEffect(() => {
    const element = dialog.current;
    const opener =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    element?.showModal();
    return () => {
      element?.close();
      if (opener?.isConnected) opener.focus();
    };
  }, []);

  async function checkout() {
    if (existing?.status === "purchased") {
      setOrder(existing);
      return;
    }
    if (busy || !reviewed || !demoAcknowledged) return;
    setBusy(true);
    setError("");
    try {
      setOrder(await purchaseFlow.start(tender));
    } catch (failure) {
      setError(
        failure instanceof Error
          ? failure.message
          : "Could not start checkout.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <dialog
      ref={dialog}
      className="tender-dialog"
      onClose={onClose}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
      aria-labelledby="tender-dialog-title"
    >
      <div className="drawer-content">
        <div className="drawer-top">
          <span className="eyebrow">
            {order ? "DEMO CHECKOUT" : "REVIEW TENDER"}
          </span>
          <button
            className="icon-button"
            aria-label="Close tender review"
            onClick={onClose}
          >
            <Icon name="close" size={21} />
          </button>
        </div>
        <div className="drawer-heading">
          <AvailabilityBadge status={availability} />
          <h2 id="tender-dialog-title">{tender.title}</h2>
          <p>
            {tender.issuer} <span>·</span> {tender.reference}
          </p>
          <dl className="drawer-facts">
            <div>
              <dt>Submission deadline</dt>
              <dd>
                {tender.deadlineText ?? "Not provided"}
                <small>As published by the issuer</small>
              </dd>
            </div>
            <div>
              <dt>Official documents</dt>
              <dd>
                {tender.pdfUrls.length}
                <small>{tender.amendmentUrls.length} amendment links</small>
              </dd>
            </div>
            <div>
              <dt>Issuer’s tender fee</dt>
              <dd>
                Check official notice
                <small>No fee extracted from this listing</small>
              </dd>
            </div>
          </dl>
          <div className="drawer-heading-bottom">
            <span className="muted">
              {order
                ? "Review → Demo checkout → Receipt"
                : "Review the notice, then choose your next step."}
            </span>
            <button
              className={`button button-secondary button-small ${savedIds.includes(tender.id) ? "button-selected" : ""}`}
              aria-pressed={savedIds.includes(tender.id)}
              onClick={() => toggleSaved(tender.id)}
            >
              <Icon name="bookmark" size={15} />
              {savedIds.includes(tender.id) ? "Saved" : "Save for later"}
            </button>
          </div>
        </div>
        {order ? (
          <DemoCheckout
            key={order.id}
            initialOrder={order}
            onBack={() => setOrder(null)}
          />
        ) : (
          <div className="drawer-body tender-review-body">
            <section aria-labelledby="review-documents-heading">
              <h3 id="review-documents-heading">
                1. Review the official documents
              </h3>
              <p className="muted">
                Check the specifications, eligibility, fee, EMD and submission
                instructions in the source notice.
              </p>
              {tender.pdfUrls.map((url, index) => (
                <a
                  className="document-card"
                  key={url}
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                >
                  <Icon name="document" size={22} />
                  <span>
                    <strong>Tender document {index + 1}</strong>
                    <small>Official PDF · opens in a new tab</small>
                  </span>
                  <Icon name="arrow" size={17} />
                </a>
              ))}
              {tender.amendmentUrls.map((url, index) => (
                <a
                  className="document-card"
                  key={url}
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                >
                  <Icon name="history" size={22} />
                  <span>
                    <strong>Amendment {index + 1}</strong>
                    <small>Read this alongside the original notice</small>
                  </span>
                  <Icon name="arrow" size={17} />
                </a>
              ))}
              <a
                className="document-card"
                href={tender.sourceUrl}
                target="_blank"
                rel="noreferrer"
              >
                <Icon name="globe" size={22} />
                <span>
                  <strong>Official tender listing</strong>
                  <small>{new URL(tender.sourceUrl).hostname}</small>
                </span>
                <Icon name="arrow" size={17} />
              </a>
              <p className="review-source-note">
                Collected by TinyFish on{" "}
                {new Date(tender.retrievedAt).toLocaleString("en-GB", {
                  timeZone: "Asia/Kolkata",
                })}{" "}
                IST. Check the source for updates. Eligibility has not been
                automatically verified.
              </p>
            </section>
            <section aria-labelledby="review-supplier-heading">
              <h3 id="review-supplier-heading">
                2. Check your supplier details
              </h3>
              <dl className="checkout-summary">
                <div>
                  <dt>Google account</dt>
                  <dd>{user?.email ?? "Sign in to continue"}</dd>
                </div>
                <div>
                  <dt>Business</dt>
                  <dd>
                    {user && profileComplete
                      ? profile.company
                      : "Complete and save your profile"}
                  </dd>
                </div>
                <div>
                  <dt>DigiLocker identity</dt>
                  <dd>
                    {identityVerified
                      ? "Verified"
                      : "Optional for demo checkout"}
                  </dd>
                </div>
              </dl>
              <Link
                className="text-link"
                href="/dashboard/profile"
                onClick={onClose}
              >
                Manage profile & DigiLocker <Icon name="arrowRight" size={15} />
              </Link>
              <p className="review-source-note">
                DigiLocker verification stays available in your profile. An
                unverified identity can try this demo and remains labelled
                unverified on the receipt.
              </p>
            </section>
            <section
              className="checkout-card"
              aria-labelledby="review-purchase-heading"
            >
              <span className="subtle-tag">
                HACKATHON DEMO · NO REAL CHARGE
              </span>
              <h3 id="review-purchase-heading">3. Buy in the demo</h3>
              <p>
                Try a simulated purchase for <strong>₹499</strong>. This is a
                demo amount, not the issuer’s fee. It does not submit a bid,
                reserve an opportunity or award a contract.
              </p>
              {existing?.status === "purchased" ? (
                <button
                  className="button button-primary"
                  onClick={() => void checkout()}
                >
                  <Icon name="checkCircle" size={17} />
                  View demo receipt
                </button>
              ) : (
                <>
                  {availability !== "open" && (
                    <div className="inline-notice" role="status">
                      {availability === "closed"
                        ? "This tender has closed. You can review or save its documents; checkout is unavailable."
                        : "The closing date is unconfirmed. Check the official notice before checkout."}
                    </div>
                  )}
                  <label className="checkout-consent">
                    <input
                      type="checkbox"
                      checked={reviewed}
                      onChange={(event) => setReviewed(event.target.checked)}
                      disabled={availability !== "open"}
                    />
                    <span>
                      I have reviewed the official notice and any amendments.
                    </span>
                  </label>
                  <label className="checkout-consent">
                    <input
                      type="checkbox"
                      checked={demoAcknowledged}
                      onChange={(event) =>
                        setDemoAcknowledged(event.target.checked)
                      }
                      disabled={availability !== "open"}
                    />
                    <span>
                      I understand this is a simulated purchase with no real
                      payment or bid submission.
                    </span>
                  </label>
                  {!user ? (
                    <button
                      className="button button-primary"
                      disabled={busy}
                      onClick={async () => {
                        setBusy(true);
                        setError("");
                        try {
                          await signInWithGoogle();
                        } catch {
                          setError(
                            "Google sign-in did not finish. Please try again.",
                          );
                        } finally {
                          setBusy(false);
                        }
                      }}
                    >
                      Sign in with Google
                    </button>
                  ) : !profileComplete ? (
                    <Link
                      className="button button-primary"
                      href="/dashboard/profile"
                      onClick={onClose}
                    >
                      Complete supplier profile{" "}
                      <Icon name="arrowRight" size={16} />
                    </Link>
                  ) : (
                    <button
                      className="button button-primary"
                      disabled={
                        busy ||
                        !reviewed ||
                        !demoAcknowledged ||
                        availability !== "open"
                      }
                      aria-busy={busy}
                      onClick={() => void checkout()}
                    >
                      {busy
                        ? "Starting checkout…"
                        : "Continue to demo checkout"}
                      <Icon name="arrowRight" size={16} />
                    </button>
                  )}
                </>
              )}
              {error && (
                <div className="error-banner" role="alert">
                  {error}
                </div>
              )}
            </section>
          </div>
        )}
      </div>
    </dialog>
  );
}
