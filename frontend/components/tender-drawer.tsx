"use client";

import { useEffect, useRef, useState } from "react";
import { DEMO_CLOCK, SAMPLE_CHANGES } from "@/lib/demo-data";
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
  const { profile, savedIds, toggleSaved, evaluationTime } = useWorkspace();
  const [tab, setTab] = useState("readiness");
  const sample = tender.provenance === "sample";
  const evaluation = evaluateTender(
    tender,
    profile,
    new Date(sample ? DEMO_CLOCK : evaluationTime),
  );
  const changes = sample
    ? SAMPLE_CHANGES.filter((change) => change.tenderId === tender.id)
    : [];

  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => element?.close();
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
          <div className="drawer-heading-bottom">
            <StatusBadge status={evaluation.status} />
            <button
              className={`button button-outline button-small ${savedIds.includes(tender.id) ? "button-selected" : ""}`}
              onClick={() => toggleSaved(tender.id)}
            >
              <Icon name="bookmark" size={15} />
              {savedIds.includes(tender.id) ? "Saved" : "Save tender"}
            </button>
          </div>
        </div>
        <div className={`provenance-banner ${sample ? "" : "provenance-live"}`}>
          <Icon name={sample ? "help" : "globe"} size={16} />
          <span>
            {sample
              ? "Illustrative sample. Clauses, values, and pages are synthetic. Checked at the demo clock: 24 Oct 2026."
              : "Collected live with TinyFish. PDF extraction and clause verification are pending; readiness is unresolved."}
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
                  : `Changes${changes.length ? ` (${changes.length})` : ""}`}
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
                      href={`/samples/${tender.id}#page-${finding.condition.page}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <Icon name="document" size={14} />
                      Sample clause {finding.condition.clause} · page{" "}
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
            {sample ? (
              <a
                className="document-card"
                href={`/samples/${tender.id}`}
                target="_blank"
                rel="noreferrer"
              >
                <span className="document-card-icon">
                  <Icon name="document" size={25} />
                </span>
                <span>
                  <strong>Illustrative tender document</strong>
                  <small>Synthetic clauses · physical page references</small>
                </span>
                <Icon name="arrow" size={18} />
              </a>
            ) : (
              tender.pdfUrls.map((url, index) => (
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
                    <small>Live URL · extraction pending</small>
                  </span>
                  <Icon name="arrow" size={17} />
                </a>
              ))
            )}
            {!sample && !tender.pdfUrls.length && (
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
                <span>Collection mode</span>
                <strong>
                  {sample ? "Synthetic sample" : "TinyFish live discovery"}
                </strong>
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
                <strong>
                  {sample
                    ? "Illustrative only"
                    : "PDF clause verification pending"}
                </strong>
              </div>
            </div>
          </div>
        )}
        {tab === "changes" && (
          <div className="drawer-body">
            <h3>Every change, in context.</h3>
            {changes.length ? (
              changes.map((change) => (
                <article className="change-detail" key={change.id}>
                  <span className="eyebrow">
                    SYNTHETIC AMENDMENT · {change.date}
                  </span>
                  <h4>{change.field}</h4>
                  <div className="before-after">
                    <div>
                      <small>BEFORE</small>
                      <span>{change.before}</span>
                    </div>
                    <Icon name="arrowRight" size={18} />
                    <div>
                      <small>AFTER</small>
                      <strong>{change.after}</strong>
                    </div>
                  </div>
                  <p>{change.detail}</p>
                  <span className="muted">
                    <Icon name="document" size={14} />
                    {change.clause} · illustrative evidence
                  </span>
                </article>
              ))
            ) : (
              <div className="empty-state">
                <Icon name="history" size={30} />
                <h3>No compared amendments yet.</h3>
                <p>
                  {tender.amendmentUrls.length
                    ? `${tender.amendmentUrls.length} amendment link(s) found. Document comparison is pending.`
                    : "No change comparison is available for this notice."}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </dialog>
  );
}
