"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { sourceReviewVersion, tenderAvailability } from "@/lib/purchases";
import { Icon, type IconName } from "./icon";
import { AvailabilityBadge, TenderDrawer } from "./tender-drawer";
import { useWorkspace } from "./workspace-provider";

function StatCard({
  label,
  value,
  icon,
  detail,
}: {
  label: string;
  value: number | null;
  icon: IconName;
  detail: string;
}) {
  return (
    <div className="stat-card stat-neutral">
      <div>
        <span>{label}</span>
        <span className="stat-icon">
          <Icon name={icon} size={18} />
        </span>
      </div>
      <strong aria-busy={value === null}>
        {value === null ? "—" : String(value).padStart(2, "0")}
      </strong>
      <p>
        <span className="stat-dot" />
        {detail}
      </p>
    </div>
  );
}

export function TenderExplorer({
  mode = "overview",
}: {
  mode?: "overview" | "discover" | "saved";
}) {
  const {
    tenders,
    profile,
    savedIds,
    toggleSaved,
    refresh,
    job,
    discoveryError,
    evaluationTime,
    catalogRetrievedAt,
    purchaseFlow,
    ready,
  } = useWorkspace();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"all" | "open" | "closed" | "unknown">(
    "all",
  );
  const [sort, setSort] = useState("deadline");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const searchInput = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if (
        event.key === "/" &&
        !(
          event.target instanceof HTMLElement &&
          (event.target.isContentEditable ||
            ["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName))
        )
      ) {
        event.preventDefault();
        searchInput.current?.focus();
      }
    };
    document.addEventListener("keydown", shortcut);
    return () => document.removeEventListener("keydown", shortcut);
  }, []);
  const isRunning = !!job && ["submitting", "running"].includes(job.status);
  const now = new Date(evaluationTime);
  const base =
    mode === "saved"
      ? tenders.filter((tender) => savedIds.includes(tender.id))
      : tenders;
  const visible = base
    .filter(
      (tender) =>
        (filter === "all" || tenderAvailability(tender, now) === filter) &&
        `${tender.title} ${tender.reference} ${tender.category}`
          .toLowerCase()
          .includes(query.toLowerCase()),
    )
    .sort((a, b) => {
      if (sort === "title") return a.title.localeCompare(b.title);
      const rank = { open: 0, unknown: 1, closed: 2 };
      return (
        rank[tenderAvailability(a, now)] - rank[tenderAvailability(b, now)] ||
        (a.deadline ?? "9999").localeCompare(b.deadline ?? "9999")
      );
    });
  const selected = tenders.find((tender) => tender.id === selectedId);
  const purchased = purchaseFlow.orders.filter(
    (order) => order.status === "purchased",
  );

  return (
    <>
      <div className="workspace-heading">
        <div>
          <div className="eyebrow">FIND → REVIEW → BUY</div>
          <h1>
            {mode === "saved"
              ? "Your saved tenders."
              : mode === "discover"
                ? "Find your next tender."
                : "Your next tender, one step at a time."}
          </h1>
          <p>
            {mode === "saved"
              ? "Come back to a notice, review its documents and continue to demo checkout."
              : "Find official notices with TinyFish, review the documents and try a demo purchase."}
          </p>
        </div>
        <button
          className="button button-primary button-small"
          onClick={() => void refresh()}
          disabled={isRunning}
          aria-busy={isRunning}
        >
          <Icon name="refresh" size={16} className={isRunning ? "spin" : ""} />
          {isRunning ? "Fetching tenders…" : "Fetch tenders"}
        </button>
      </div>
      {discoveryError && (
        <div className="error-banner" role="alert">
          <Icon name="alert" size={18} />
          <span>{discoveryError}</span>
          <Link href="/dashboard/sources">
            Source settings <Icon name="arrowRight" size={14} />
          </Link>
        </div>
      )}
      {mode === "overview" && (
        <>
          <nav className="supplier-steps" aria-label="Supplier workflow">
            {[
              {
                href: "/dashboard/profile",
                title: "Create your profile",
                detail: "Sign in with Google and save your business details.",
              },
              {
                href: "/dashboard/profile#document-verification",
                title: "Verify with DigiLocker",
                detail: "Connect your identity. Optional for demo checkout.",
              },
              {
                href: "/dashboard/tenders",
                title: "Find & review",
                detail: "Read the notice, deadline and official documents.",
              },
              {
                href: "/dashboard/purchases",
                title: "Buy in the demo",
                detail: "Simulate payment and keep your receipt in My tenders.",
              },
            ].map((step, index) => (
              <Link key={step.title} href={step.href}>
                <b>{index + 1}</b>
                <span>
                  <strong>{step.title}</strong>
                  <small>{step.detail}</small>
                </span>
              </Link>
            ))}
          </nav>
          <div className="stats-grid">
            <StatCard
              label="Fetched tenders"
              value={ready ? tenders.length : null}
              icon="document"
              detail="Official IIIT-Delhi notices"
            />
            <StatCard
              label="Open for review"
              value={
                ready
                  ? tenders.filter(
                      (tender) => tenderAvailability(tender, now) === "open",
                    ).length
                  : null
              }
              icon="clock"
              detail="Submission deadline has not passed"
            />
            <StatCard
              label="Saved for later"
              value={
                ready
                  ? tenders.filter((tender) => savedIds.includes(tender.id))
                      .length
                  : null
              }
              icon="bookmark"
              detail="Your personal shortlist"
            />
            <StatCard
              label="Demo purchased"
              value={ready && !purchaseFlow.loading ? purchased.length : null}
              icon="checkCircle"
              detail="Simulated purchases · no real charge"
            />
          </div>
        </>
      )}
      <div
        className={`workspace-grid ${mode !== "overview" ? "workspace-grid-full" : ""}`}
      >
        <section className="tender-list-section">
          <div className="section-title-row">
            <div>
              <h2>
                {mode === "saved"
                  ? "Your saved shortlist"
                  : "Your tender shortlist"}
                <span>{base.length}</span>
              </h2>
              <p>Open a tender to review the documents and buy in the demo.</p>
            </div>
          </div>
          <div className="list-toolbar">
            <label className="search-field">
              <Icon name="search" size={17} />
              <input
                ref={searchInput}
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search tenders or references…"
                aria-label="Search tenders"
              />
              <kbd>/</kbd>
            </label>
          </div>
          <div className="list-tabs-row">
            <div className="list-tabs" aria-label="Filter by closing status">
              {(
                [
                  { id: "all", label: "All tenders" },
                  { id: "open", label: "Open" },
                  { id: "closed", label: "Closed" },
                  { id: "unknown", label: "Date unconfirmed" },
                ] as const
              ).map((tab) => (
                <button
                  key={tab.id}
                  className={filter === tab.id ? "selected" : ""}
                  aria-pressed={filter === tab.id}
                  onClick={() => setFilter(tab.id)}
                >
                  {tab.label}
                  <span>
                    {tab.id === "all"
                      ? base.length
                      : base.filter(
                          (tender) =>
                            tenderAvailability(tender, now) === tab.id,
                        ).length}
                  </span>
                </button>
              ))}
            </div>
            <label className="sort-control">
              <span>Sort:</span>
              <select
                value={sort}
                onChange={(event) => setSort(event.target.value)}
                aria-label="Sort tenders"
              >
                <option value="deadline">Closing soon</option>
                <option value="title">Title</option>
              </select>
            </label>
          </div>
          <div className="table-scroll">
            <table className="tender-table">
              <thead>
                <tr>
                  <th>Tender / opportunity</th>
                  <th>Status</th>
                  <th>Closing date</th>
                  <th>
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody aria-busy={!ready}>
                {!ready &&
                  [0, 1, 2].map((row) => (
                    <tr key={row} className="skeleton-row">
                      <td className="cell-title">
                        <span className="skeleton skeleton-title" />
                        <span className="skeleton skeleton-meta" />
                      </td>
                      <td className="cell-status">
                        <span className="skeleton skeleton-badge" />
                      </td>
                      <td className="cell-deadline">
                        <span className="skeleton skeleton-date" />
                      </td>
                      <td className="cell-actions" />
                    </tr>
                  ))}
                {ready &&
                  visible.map((tender) => (
                    <tr key={tender.id}>
                      <td className="cell-title">
                        <div className="tender-title-cell">
                          <span className="tender-category-icon category-it">
                            <Icon name="document" size={19} />
                          </span>
                          <div>
                            <button
                              className="tender-title"
                              onClick={() => setSelectedId(tender.id)}
                            >
                              {tender.title}
                            </button>
                            <div className="tender-meta">
                              <span>{tender.issuer}</span>
                              <i />
                              {tender.reference}
                              {tender.amendmentUrls.length > 0 && (
                                <span className="amended-label">
                                  <Icon name="history" size={11} />
                                  Amendments
                                </span>
                              )}
                            </div>
                            {purchased.some(
                              (order) => order.tender.id === tender.id,
                            ) && (
                              <span className="tender-purchase-label">
                                Demo purchased · receipt saved
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="cell-status">
                        <AvailabilityBadge
                          status={tenderAvailability(tender, now)}
                        />
                      </td>
                      <td className="cell-deadline">
                        <span className="deadline-date">
                          {tender.deadline
                            ? new Date(tender.deadline).toLocaleDateString(
                                "en-GB",
                                {
                                  day: "2-digit",
                                  month: "short",
                                  year: "numeric",
                                  timeZone: "Asia/Kolkata",
                                },
                              )
                            : (tender.deadlineText ?? "Unconfirmed")}
                        </span>
                        <span className="deadline-time">
                          {tender.deadline
                            ? `${new Date(tender.deadline).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", timeZone: "Asia/Kolkata" })} IST`
                            : "Check source"}
                        </span>
                      </td>
                      <td className="cell-actions">
                        <div className="row-actions">
                          <button
                            className={`icon-button save-button ${savedIds.includes(tender.id) ? "is-saved" : ""}`}
                            onClick={() => toggleSaved(tender.id)}
                            aria-label={`${savedIds.includes(tender.id) ? "Unsave" : "Save"} ${tender.title}`}
                            aria-pressed={savedIds.includes(tender.id)}
                          >
                            <Icon name="bookmark" size={17} />
                          </button>
                          <button
                            className="button button-secondary button-small"
                            onClick={() => setSelectedId(tender.id)}
                            aria-label={`Review ${tender.title}`}
                          >
                            Review
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
          {ready && !visible.length && (
            <div className="empty-state">
              <Icon name={mode === "saved" ? "bookmark" : "search"} size={32} />
              <h3>
                {mode === "saved" && !base.length
                  ? "No saved tenders yet."
                  : "No tenders match these filters."}
              </h3>
              <p>
                {mode === "saved" && !base.length
                  ? "Save a notice from Discover tenders to find it here."
                  : "Try another search or reset your filters."}
              </p>
              {mode === "saved" && !base.length ? (
                <Link
                  className="button button-secondary button-small"
                  href="/dashboard/tenders"
                >
                  Discover tenders
                </Link>
              ) : (
                <button
                  className="button button-secondary button-small"
                  onClick={() => {
                    setQuery("");
                    setFilter("all");
                  }}
                >
                  Reset filters
                </button>
              )}
            </div>
          )}
          <div className="table-footer">
            <span role="status">
              {ready
                ? `Showing ${visible.length} of ${base.length} tenders`
                : "Loading your workspace…"}
            </span>
            <span>
              <Icon name="link" size={13} />
              TinyFish snapshot ·{" "}
              {new Date(catalogRetrievedAt).toLocaleDateString("en-GB", {
                timeZone: "Asia/Kolkata",
              })}
            </span>
          </div>
        </section>
        {mode === "overview" && (
          <aside className="workspace-aside">
            <section className="supplier-card">
              <div className="aside-card-heading">
                <span className="eyebrow">YOUR BUSINESS</span>
                <Icon name="building" size={18} />
              </div>
              <h3>{profile.company || "Set up your supplier profile"}</h3>
              <p>{profile.contact || "Add a contact person"}</p>
              <div className="supplier-categories">
                {profile.categories.map((category) => (
                  <span key={category}>{category}</span>
                ))}
              </div>
              <Link
                href="/dashboard/profile"
                className="button button-secondary button-small"
              >
                Profile & DigiLocker <Icon name="arrowRight" size={15} />
              </Link>
            </section>
            <section className="source-mini-card">
              <div className="aside-card-heading">
                <span className="eyebrow">MY TENDERS</span>
                <Icon name="checkCircle" size={18} />
              </div>
              <p>
                Your demo purchases and receipts stay together in your account.
              </p>
              <Link className="text-link" href="/dashboard/purchases">
                View My tenders <Icon name="arrowRight" size={14} />
              </Link>
            </section>
            <section className="source-mini-card">
              <div className="aside-card-heading">
                <span className="eyebrow">DISCOVERY SOURCE</span>
                <Icon name="globe" size={18} />
              </div>
              <div className="source-mini-heading">
                <span className="source-avatar">II</span>
                <div>
                  <strong>IIIT-Delhi</strong>
                  <small>Public tender portal · TinyFish</small>
                </div>
              </div>
              <Link className="text-link" href="/dashboard/sources">
                Manage source <Icon name="arrowRight" size={14} />
              </Link>
            </section>
          </aside>
        )}
      </div>
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
