"use client";

import { useEffect, useState } from "react";
import { Icon } from "@/components/icon";
import { useWorkspace } from "@/components/workspace-provider";
import type { DiscoveryJob } from "@/lib/types";

const RUN_STATUS: Record<
  DiscoveryJob["status"],
  { label: string; tone: "meets" | "info" | "review" | "blocked" }
> = {
  completed: { label: "Completed", tone: "meets" },
  running: { label: "Running", tone: "info" },
  submitting: { label: "Starting", tone: "info" },
  failed: { label: "Failed", tone: "blocked" },
  cancelled: { label: "Cancelled", tone: "review" },
  submission_unknown: { label: "Needs reconciliation", tone: "review" },
};

function formatRunTime(value: string) {
  return `${new Date(value).toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: "Asia/Kolkata",
  })} IST`;
}

export default function SourcesPage() {
  const { refresh, job, discoveryError, collectionMode } = useWorkspace();
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [tokenRequired, setTokenRequired] = useState(false);
  const [accessToken, setAccessToken] = useState("");
  const isRunning = !!job && ["submitting", "running"].includes(job.status);
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/discovery", { signal: controller.signal })
      .then((response) => response.json())
      .then((value) => {
        setConfigured(value.configured);
        setTokenRequired(value.tokenRequired);
      })
      .catch(() => {
        if (!controller.signal.aborted) setConfigured(false);
      });
    return () => controller.abort();
  }, []);
  return (
    <>
      <div className="workspace-heading">
        <div>
          <div className="eyebrow">GOOD EVIDENCE STARTS AT THE SOURCE</div>
          <h1>A connected view of opportunity.</h1>
          <p>
            Public tender notices, collected with TinyFish. Your profile stays
            in your workspace.
          </p>
        </div>
        <span className="subtle-tag">
          <Icon name="globe" size={14} />
          One focused source
        </span>
      </div>
      <section className="source-card">
        <div className="source-card-heading">
          <div>
            <span className="source-avatar">II</span>
            <div>
              <h2>IIIT-Delhi</h2>
              <p>Institutional procurement · Public tender portal</p>
            </div>
          </div>
          <span className="subtle-tag" role="status">
            <span
              className={`live-dot ${configured === null ? "is-idle" : configured ? "" : "is-warning"}`}
            />
            {configured === null
              ? "Checking configuration…"
              : configured
                ? "API key configured"
                : "Setup needed"}
          </span>
        </div>
        <p>
          TinyFish reads the public listing and returns relevant notices,
          document URLs, deadline text, and visible amendment links. A source
          run discovers up to five notices. PDF extraction and automatic
          amendment comparison are the next backend milestone.
        </p>
        <div className="source-details">
          <div>
            <small>SOURCE URL</small>
            <a
              href="https://iiitd.ac.in/tenders"
              target="_blank"
              rel="noreferrer"
            >
              <strong>
                iiitd.ac.in/tenders <Icon name="arrow" size={12} />
              </strong>
            </a>
          </div>
          <div>
            <small>COLLECTION MODE</small>
            <strong>Public, read-only discovery</strong>
          </div>
          <div>
            <small>WORKSPACE DATA</small>
            <strong>
              {collectionMode === "live"
                ? "Live discovery snapshot"
                : "Illustrative sample notices"}
            </strong>
          </div>
        </div>
        {!configured && configured !== null && (
          <div className="inline-notice">
            <Icon name="help" size={17} />
            <p>
              Set <code>TINYFISH_API_KEY</code> in{" "}
              <code>frontend/.env.local</code> or your server environment, then
              restart the development server. The key is only read on the server
              and is never sent to this browser.
            </p>
          </div>
        )}
        {tokenRequired && (
          <label className="source-access-field">
            Workspace discovery access token
            <input
              type="password"
              value={accessToken}
              onChange={(event) => setAccessToken(event.target.value)}
              autoComplete="off"
              placeholder="Enter the workspace access token"
            />
            <small>
              Required for a hosted workspace. This token is only kept in this
              page’s memory.
            </small>
          </label>
        )}
        <div className="source-actions">
          <button
            className="button button-primary button-small"
            disabled={isRunning || configured === false || configured === null}
            aria-busy={isRunning}
            onClick={() => void refresh(accessToken)}
          >
            <Icon
              name="refresh"
              size={16}
              className={isRunning ? "spin" : ""}
            />
            {isRunning ? "TinyFish is reading…" : "Run live discovery"}
          </button>
          <a
            className="text-link"
            href="https://iiitd.ac.in/tenders"
            target="_blank"
            rel="noreferrer"
          >
            Visit public source <Icon name="arrow" size={14} />
          </a>
        </div>
        <p className="muted">
          Each live run uses your TinyFish account quota. Discovery runs are
          user initiated; opening the workspace does not start a run.
        </p>
        {discoveryError && (
          <div className="error-banner" role="alert">
            <Icon name="alert" size={16} />
            {discoveryError}
          </div>
        )}
      </section>
      <section className="source-history">
        <h2>Latest application run</h2>
        {job ? (
          <>
            <dl className="run-record">
              <div>
                <dt>Status</dt>
                <dd>
                  <span
                    className={`run-status run-${RUN_STATUS[job.status].tone}`}
                  >
                    {RUN_STATUS[job.status].label}
                  </span>
                </dd>
              </div>
              <div>
                <dt>Application job</dt>
                <dd>
                  <code>{job.id}</code>
                </dd>
              </div>
              <div>
                <dt>TinyFish run</dt>
                <dd>
                  {job.providerRunId ? (
                    <code>{job.providerRunId}</code>
                  ) : (
                    "Not assigned"
                  )}
                </dd>
              </div>
              <div>
                <dt>Started</dt>
                <dd>{formatRunTime(job.createdAt)}</dd>
              </div>
              <div>
                <dt>Finished</dt>
                <dd>
                  {job.finishedAt
                    ? formatRunTime(job.finishedAt)
                    : "In progress"}
                </dd>
              </div>
              <div>
                <dt>Notices</dt>
                <dd>{job.tenders ? job.tenders.length : "—"}</dd>
              </div>
              {job.error && (
                <div className="run-record-message">
                  <dt>Message</dt>
                  <dd>{job.error}</dd>
                </div>
              )}
            </dl>
            <p className="muted">
              Completed live notices stay Review needed until source clauses are
              extracted and verified.
            </p>
          </>
        ) : (
          <p className="muted">
            No application run yet. Your sample workspace is ready to explore in
            the meantime.
          </p>
        )}
      </section>
    </>
  );
}
