"use client";

import { useEffect, useRef, useState } from "react";
import { evaluateTender } from "@/lib/rules";
import type { Tender } from "@/lib/types";
import { Icon } from "./icon";
import { StatusBadge } from "./status-badge";
import { useWorkspace } from "./workspace-provider";

export function TenderDrawer({
  tender,
  onClose,
}: {
  tender: Tender;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const {
    profile,
    savedIds,
    toggleSaved,
    evaluationTime,
    verifiedCertificates,
  } = useWorkspace();
  const [tab, setTab] = useState("readiness");
  const evaluation = evaluateTender(
    tender,
    profile,
    new Date(evaluationTime),
    verifiedCertificates,
  );
  const deadline = tender.deadline ? new Date(tender.deadline) : null;
  const checkCounts = {
    meets: evaluation.findings.filter((finding) => finding.status === "meets")
      .length,
    review: evaluation.findings.filter((finding) => finding.status === "review")
      .length,
    blocked: evaluation.findings.filter(
      (finding) => finding.status === "blocked",
    ).length,
  };

  useEffect(() => {
    const element = dialog.current;
    // Return focus to whatever opened the review once it closes.
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
          <span className="eyebrow">TENDER REVIEW</span>
          <button
            className="icon-button"
            aria-label="Close tender review"
            onClick={onClose}
          >
            <Icon name="close" size={21} />
          </button>
        </div>
        <div className="drawer-heading">
          <span className="category-pill">{tender.category}</span>
          <h2 id="tender-dialog-title">{tender.title}</h2>
          <p>
            {tender.issuer} <span>·</span> {tender.reference}
          </p>
          <dl className="drawer-facts">
            <div>
              <dt>Closes</dt>
              <dd>
                {deadline
                  ? deadline.toLocaleDateString("en-GB", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                      timeZone: "Asia/Kolkata",
                    })
                  : (tender.deadlineText ?? "Not stated")}
                <small>
                  {deadline
                    ? `${deadline.toLocaleTimeString("en-US", {
                        hour: "numeric",
                        minute: "2-digit",
                        hour12: true,
                        timeZone: "Asia/Kolkata",
                      })} IST`
                    : "As listed · verify source"}
                </small>
              </dd>
            </div>
            <div>
              <dt>Estimated value</dt>
              <dd>
                {tender.value}
                <small>PDF extraction pending</small>
              </dd>
            </div>
            <div>
              <dt>Checks</dt>
              <dd>
                {evaluation.findings.length
                  ? `${checkCounts.meets} of ${evaluation.findings.length} meet`
                  : "None extracted"}
                <small>
                  {evaluation.findings.length
                    ? [
                        checkCounts.review && `${checkCounts.review} to review`,
                        checkCounts.blocked && `${checkCounts.blocked} blocked`,
                      ]
                        .filter(Boolean)
                        .join(" · ") || "No open issues"
                    : "PDF checks pending"}
                </small>
              </dd>
            </div>
          </dl>
          <div className="drawer-heading-bottom">
            <StatusBadge status={evaluation.status} />
            <button
              className={`button button-secondary button-small ${savedIds.includes(tender.id) ? "button-selected" : ""}`}
              onClick={() => toggleSaved(tender.id)}
            >
              <Icon name="bookmark" size={15} />
              {savedIds.includes(tender.id) ? "Saved" : "Save tender"}
            </button>
          </div>
        </div>
        <div className="provenance-banner provenance-live">
          <Icon name="globe" size={16} />
          <span>
            Collected from the official source with TinyFish. PDF extraction and
            clause verification are pending; readiness is unresolved.
          </span>
        </div>
        <div className="drawer-tabs" aria-label="Tender review sections">
          {["readiness", "evidence", "changes"].map((value) => (
            <button
              key={value}
              className={value === tab ? "selected" : ""}
              aria-pressed={tab === value}
              onClick={() => setTab(value)}
            >
              {value === "readiness"
                ? "Readiness checks"
                : value === "evidence"
                  ? "Source evidence"
                  : "Amendment links"}
            </button>
          ))}
        </div>
        {tab === "readiness" && (
          <div className="drawer-body">
            <div className="drawer-summary">
              <h3>What fits. What needs a closer look.</h3>
              <p>Requirements compared with your current supplier profile.</p>
            </div>
            {!evaluation.coverageComplete && (
              <div className="inline-notice">
                <Icon name="alert" size={18} />
                <p>
                  Clause coverage is incomplete. Download the source documents
                  and review all five condition groups before relying on a
                  readiness result.
                </p>
              </div>
            )}
            {!evaluation.findings.length && (
              <a
                className="document-card"
                href={tender.pdfUrls[0] ?? tender.sourceUrl}
                target="_blank"
                rel="noreferrer"
              >
                <Icon name="document" size={22} />
                Review the official tender document
                <Icon name="arrow" size={17} />
              </a>
            )}
            <div className="condition-list">
              {evaluation.findings.map((finding) => (
                <details
                  className="condition-item"
                  key={finding.condition.type}
                >
                  <summary>
                    <span
                      className={`condition-status-icon status-${finding.status}`}
                    >
                      <Icon
                        name={
                          finding.status === "meets"
                            ? "check"
                            : finding.status === "blocked"
                              ? "close"
                              : "clock"
                        }
                        size={16}
                      />
                    </span>
                    <span>
                      <strong>{finding.condition.label}</strong>
                      <small>{finding.condition.requirement}</small>
                    </span>
                    <StatusBadge status={finding.status} short />
                    <Icon name="chevronDown" size={16} />
                  </summary>
                  <div className="condition-detail">
                    <div>
                      <span>YOUR PROFILE</span>
                      <strong>{finding.supplierValue}</strong>
                    </div>
                    <p>{finding.reason}</p>
                    <blockquote>“{finding.condition.quote}”</blockquote>
                    <a
                      href={`${tender.pdfUrls[0] ?? tender.sourceUrl}#page=${finding.condition.page}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <Icon name="document" size={14} />
                      Source clause {finding.condition.clause} · page{" "}
                      {finding.condition.page}
                      <Icon name="arrow" size={13} />
                    </a>
                  </div>
                </details>
              ))}
            </div>
            <div className="decision-note">
              <Icon name="shield" size={19} />
              <p>
                <strong>You make the final call.</strong> Meets checked
                conditions describes the supported checks. Always review the
                full notice and applicable terms before bidding.
              </p>
            </div>
          </div>
        )}
        {tab === "evidence" && (
          <div className="drawer-body">
            <h3>Keep the source within reach.</h3>
            <p className="muted">
              Evidence should be easy to inspect, not just easy to trust.
            </p>
            {tender.pdfUrls.map((url, index) => (
              <a
                className="document-card"
                key={url}
                href={url}
                target="_blank"
                rel="noreferrer"
              >
                <Icon name="document" size={24} />
                <span>
                  <strong>Source PDF {index + 1}</strong>
                  <small>Official document · clause verification pending</small>
                </span>
                <Icon name="arrow" size={17} />
              </a>
            ))}
            {!tender.pdfUrls.length && (
              <div className="inline-notice">
                No PDF link was returned for this notice. Review the public
                source.
              </div>
            )}
            <a
              className="document-card"
              href={tender.sourceUrl}
              target="_blank"
              rel="noreferrer"
            >
              <span className="document-card-icon">
                <Icon name="globe" size={24} />
              </span>
              <span>
                <strong>Public tender listing</strong>
                <small>{new URL(tender.sourceUrl).hostname}</small>
              </span>
              <Icon name="arrow" size={18} />
            </a>
            <div className="evidence-metadata">
              <div>
                <span>Submission deadline (source text)</span>
                <strong>{tender.deadlineText ?? "Not provided"}</strong>
              </div>
              <div>
                <span>Collection mode</span>
                <strong>TinyFish source snapshot</strong>
              </div>
              <div>
                <span>Observation time</span>
                <strong>
                  {new Date(tender.retrievedAt).toLocaleString("en-GB", {
                    timeZone: "Asia/Kolkata",
                  })}{" "}
                  IST
                </strong>
              </div>
              <div>
                <span>Verification</span>
                <strong>PDF clause verification pending</strong>
              </div>
            </div>
          </div>
        )}
        {tab === "changes" && (
          <div className="drawer-body">
            <h3>Every change, in context.</h3>
            {tender.amendmentUrls.length ? (
              tender.amendmentUrls.map((url, index) => (
                <a
                  className="document-card"
                  key={url}
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                >
                  <Icon name="document" size={20} />
                  Amendment {index + 1} · comparison pending
                  <Icon name="arrow" size={17} />
                </a>
              ))
            ) : (
              <div className="empty-state">
                <Icon name="history" size={30} />
                <h3>No amendment links collected.</h3>
                <p>
                  Check the public source for any subsequent changes to this
                  notice.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </dialog>
  );
}
