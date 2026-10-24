"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { DEMO_CLOCK } from "@/lib/demo-data";
import { evaluateTender } from "@/lib/rules";
import type { Readiness, Tender } from "@/lib/types";
import { Icon, type IconName } from "./icon";
import { StatusBadge } from "./status-badge";
import { TenderDrawer } from "./tender-drawer";
import { useWorkspace } from "./workspace-provider";

function StatCard({
  label,
  value,
  icon,
  tone,
  detail,
}: {
  label: string;
  value: number;
  icon: IconName;
  tone: string;
  detail: string;
}) {
  return (
    <div className={`stat-card stat-${tone}`}>
      <div>
        <span>{label}</span>
        <span className="stat-icon">
          <Icon name={icon} size={18} />
        </span>
      </div>
      <strong>{String(value).padStart(2, "0")}</strong>
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
    notify,
    evaluationTime,
    collectionMode,
  } = useWorkspace();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"all" | Readiness>("all");
  const [category, setCategory] = useState("all");
  const [showFilters, setShowFilters] = useState(false);
  const [sort, setSort] = useState("relevance");
  const [selected, setSelected] = useState<Tender | null>(null);
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
  const evaluated = useMemo(
    () =>
      tenders.map((tender) => ({
        tender,
        evaluation: evaluateTender(
          tender,
          profile,
          new Date(
            tender.provenance === "sample" ? DEMO_CLOCK : evaluationTime,
          ),
        ),
      })),
    [tenders, profile, evaluationTime],
  );
  const counts = {
    meets: evaluated.filter((entry) => entry.evaluation.status === "meets")
      .length,
    review: evaluated.filter((entry) => entry.evaluation.status === "review")
      .length,
    blocked: evaluated.filter((entry) => entry.evaluation.status === "blocked")
      .length,
  };
  const base =
    mode === "saved"
      ? evaluated.filter(({ tender }) => savedIds.includes(tender.id))
      : evaluated;
  const visible = base
    .filter(
      ({ tender, evaluation }) =>
        (filter === "all" || evaluation.status === filter) &&
        (category === "all" || tender.category === category) &&
        `${tender.title} ${tender.reference} ${tender.category}`
          .toLowerCase()
          .includes(query.toLowerCase()),
    )
    .sort((a, b) =>
      sort === "deadline"
        ? (a.tender.deadline ?? "9999").localeCompare(
            b.tender.deadline ?? "9999",
          )
        : (b.tender.relevance ?? 0) - (a.tender.relevance ?? 0),
    );
  const amendments = tenders.filter((tender) => tender.amended).length;
  const completenessValues = [
    profile.company,
    profile.turnover.every((year) => year.amount !== null),
    profile.completedOrders !== null,
    profile.depositCapacity !== null,
    ...Object.values(profile.certificates).map((value) => value !== null),
  ];
  const completeness = Math.round(
    (completenessValues.filter(Boolean).length / completenessValues.length) *
      100,
  );
  const sample = collectionMode === "sample";

  function exportShortlist() {
    const data = visible.map(({ tender, evaluation }) => ({
      reference: tender.reference,
      title: tender.title,
      readiness: evaluation.status,
      provenance: tender.provenance,
      deadline: tender.deadlineText,
      source: tender.sourceUrl,
    }));
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "tenderlens-shortlist.json";
    anchor.click();
    URL.revokeObjectURL(url);
    notify(`Exported ${data.length} tenders with their provenance labels.`);
  }

  return (
    <>
      <div className="workspace-heading">
        <div>
          <div className="eyebrow">YOUR OPPORTUNITY, IN FOCUS</div>
          <h1>
            {mode === "saved"
              ? "Good opportunities. Kept close."
              : mode === "discover"
                ? "Find your next good fit."
                : "A clearer view of what’s next."}
          </h1>
          <p>
            {mode === "saved"
              ? "Your saved notices, their readiness, and everything worth another look."
              : "Discover relevant tenders. Understand your readiness. Make your next move."}
          </p>
        </div>
        <button
          className="button button-dark button-small"
          onClick={() => void refresh()}
          disabled={isRunning}
        >
          <Icon name="refresh" size={16} className={isRunning ? "spin" : ""} />
          {isRunning ? "Checking source…" : "Refresh tenders"}
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
          <div className="stats-grid">
            <StatCard
              label="Relevant tenders"
              value={tenders.length}
              icon="document"
              tone="neutral"
              detail={
                sample
                  ? "Illustrative sample notices"
                  : "From the latest source run"
              }
            />
            <StatCard
              label="Meets checked conditions"
              value={counts.meets}
              icon="checkCircle"
              tone="green"
              detail="A promising place to start"
            />
            <StatCard
              label="Review needed"
              value={counts.review}
              icon="clock"
              tone="amber"
              detail="A few details to look into"
            />
            <StatCard
              label="Blocked"
              value={counts.blocked}
              icon="shield"
              tone="red"
              detail="Know your blockers early"
            />
          </div>
          {amendments > 0 && (
            <Link href="/dashboard/amendments" className="amendment-banner">
              <span className="amendment-banner-icon">
                <Icon name="history" size={21} />
              </span>
              <span>
                <strong>A few things have changed.</strong>
                <small>
                  {amendments}{" "}
                  {sample ? "sample tenders have" : "tenders have visible"}{" "}
                  amendments worth a closer look.
                </small>
              </span>
              <b>
                Review changes <Icon name="arrowRight" size={16} />
              </b>
            </Link>
          )}
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
              <p>Relevance brings it here. Evidence helps you decide.</p>
            </div>
            <button
              className="icon-button"
              onClick={exportShortlist}
              aria-label="Export shortlist"
            >
              <Icon name="download" size={18} />
            </button>
          </div>
          <div className="list-toolbar">
            <label className="search-field">
              <Icon name="search" size={17} />
              <input
                ref={searchInput}
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search tenders, categories, references…"
                aria-label="Search tenders"
              />
              <kbd>/</kbd>
            </label>
            <button
              className={`button button-outline button-small ${showFilters ? "button-selected" : ""}`}
              aria-expanded={showFilters}
              onClick={() => setShowFilters(!showFilters)}
            >
              <Icon name="filter" size={15} />
              Filters{category !== "all" && <span className="filter-dot" />}
            </button>
          </div>
          {showFilters && (
            <div className="advanced-filters">
              <label>
                Category
                <select
                  value={category}
                  onChange={(event) => setCategory(event.target.value)}
                >
                  <option value="all">All categories</option>
                  {[...new Set(tenders.map((tender) => tender.category))].map(
                    (value) => (
                      <option key={value}>{value}</option>
                    ),
                  )}
                </select>
              </label>
              <button
                className="text-link"
                onClick={() => {
                  setCategory("all");
                  setFilter("all");
                  setQuery("");
                }}
              >
                Reset filters
              </button>
            </div>
          )}
          <div className="list-tabs-row">
            <div className="list-tabs" aria-label="Filter by readiness">
              {[
                { id: "all", label: "All tenders" },
                { id: "meets", label: "Meets checks" },
                { id: "review", label: "Review needed" },
                { id: "blocked", label: "Blocked" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  className={filter === tab.id ? "selected" : ""}
                  aria-pressed={filter === tab.id}
                  onClick={() => setFilter(tab.id as typeof filter)}
                >
                  {tab.label}
                  <span>
                    {tab.id === "all"
                      ? base.length
                      : base.filter(
                          ({ evaluation }) => evaluation.status === tab.id,
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
                <option value="relevance">Relevance</option>
                <option value="deadline">Closing soon</option>
              </select>
            </label>
          </div>
          <div className="table-scroll">
            <table className="tender-table">
              <thead>
                <tr>
                  <th>TENDER / OPPORTUNITY</th>
                  <th>READINESS</th>
                  <th>CLOSING DATE</th>
                  <th>
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {visible.map(({ tender, evaluation }) => (
                  <tr key={tender.id}>
                    <td>
                      <div className="tender-title-cell">
                        <span
                          className={`tender-category-icon category-${tender.category === "Electronics" ? "electronics" : tender.category === "IT equipment" ? "it" : "lab"}`}
                        >
                          <Icon
                            name={
                              tender.category === "IT equipment"
                                ? "grid"
                                : tender.category === "Electronics"
                                  ? "activity"
                                  : "document"
                            }
                            size={19}
                          />
                        </span>
                        <div>
                          <button
                            className="tender-title"
                            onClick={() => setSelected(tender)}
                          >
                            {tender.title}
                          </button>
                          <div className="tender-meta">
                            <span>{tender.category}</span>
                            <i />
                            {tender.reference}
                            {tender.amended && (
                              <span className="amended-label">
                                <Icon name="history" size={11} />
                                Amended
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <StatusBadge status={evaluation.status} short />
                    </td>
                    <td>
                      <span className="deadline-date">
                        {tender.deadline
                          ? new Date(tender.deadline).toLocaleDateString(
                              "en-GB",
                              {
                                day: "2-digit",
                                month: "short",
                                timeZone: "Asia/Kolkata",
                              },
                            )
                          : "Unconfirmed"}
                      </span>
                      <span className="deadline-time">
                        {tender.provenance === "sample"
                          ? "3:00 PM IST"
                          : "Verify source"}
                      </span>
                    </td>
                    <td>
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
                          className="icon-button"
                          onClick={() => setSelected(tender)}
                          aria-label={`Review ${tender.title}`}
                        >
                          <Icon name="chevron" size={17} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!visible.length && (
            <div className="empty-state">
              <Icon name={mode === "saved" ? "bookmark" : "search"} size={32} />
              <h3>
                {mode === "saved" && !base.length
                  ? "A good fit is worth keeping."
                  : "No tenders match these filters."}
              </h3>
              <p>
                {mode === "saved" && !base.length
                  ? "Save a notice from your shortlist to find it here."
                  : "Try another search or reset your filters."}
              </p>
              <button
                className="button button-outline button-small"
                onClick={() => {
                  setQuery("");
                  setCategory("all");
                  setFilter("all");
                }}
              >
                Reset filters
              </button>
            </div>
          )}
          <div className="table-footer">
            <span>
              Showing {visible.length} of {base.length} tenders
            </span>
            <span>
              <Icon name="link" size={13} />
              {sample
                ? "Sample data · demo clock: 24 Oct 2026"
                : "Live discovery · PDF checks pending"}
            </span>
          </div>
        </section>
        {mode === "overview" && (
          <aside className="workspace-aside">
            <section className="supplier-card">
              <div className="aside-card-heading">
                <span className="eyebrow">YOUR BUSINESS</span>
                <Link
                  href="/dashboard/profile"
                  aria-label="Edit supplier profile"
                >
                  <Icon name="arrow" size={16} />
                </Link>
              </div>
              <span className="supplier-card-avatar">
                <Icon name="building" size={23} />
              </span>
              <h3>{profile.company}</h3>
              <p>Independent supplier · India</p>
              <div className="profile-progress-label">
                <span>Profile completeness</span>
                <strong>{completeness}%</strong>
              </div>
              <div className="progress-track">
                <span style={{ width: `${completeness}%` }} />
              </div>
              <div className="supplier-categories">
                {profile.categories.map((value) => (
                  <span key={value}>{value}</span>
                ))}
              </div>
              <div className="profile-tip">
                <Icon name="spark" size={15} />
                <span>
                  {completeness < 100
                    ? "A certificate detail could make your next review clearer."
                    : "Your profile is ready for a more informed review."}
                </span>
              </div>
              <Link
                href="/dashboard/profile"
                className="button button-outline button-small"
              >
                Review profile <Icon name="arrowRight" size={15} />
              </Link>
            </section>
            <section className="source-mini-card">
              <div className="aside-card-heading">
                <span className="eyebrow">YOUR DISCOVERY SOURCE</span>
                <Icon name="globe" size={16} />
              </div>
              <div className="source-mini-heading">
                <span className="source-avatar">II</span>
                <div>
                  <strong>IIIT-Delhi</strong>
                  <small>Public tender portal</small>
                </div>
              </div>
              <p>
                <span className="live-dot" />
                {sample ? "Sample workspace active" : "Live snapshot available"}
              </p>
              <Link className="text-link" href="/dashboard/sources">
                Manage source <Icon name="arrowRight" size={14} />
              </Link>
            </section>
            <div className="workspace-footnote">
              <Icon name="shield" size={18} />
              <p>
                Your final bid decision stays with you. TenderLens makes the
                evidence easier to see.
              </p>
            </div>
          </aside>
        )}
      </div>
      {selected && (
        <TenderDrawer tender={selected} onClose={() => setSelected(null)} />
      )}
    </>
  );
}
