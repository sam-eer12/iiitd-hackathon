"use client";

import { useState } from "react";
import { Icon } from "@/components/icon";
import { TenderDrawer } from "@/components/tender-drawer";
import { useWorkspace } from "@/components/workspace-provider";
import { SAMPLE_CHANGES } from "@/lib/demo-data";
import type { Tender } from "@/lib/types";

export default function AmendmentsPage() {
  const { tenders, collectionMode } = useWorkspace();
  const [selected, setSelected] = useState<Tender | null>(null);
  const sample = collectionMode === "sample";
  return (
    <>
      <div className="workspace-heading">
        <div>
          <div className="eyebrow">EVERY CHANGE, IN SIGHT</div>
          <h1>A clearer view of what changed.</h1>
          <p>Before, after, and what it means for your next bid.</p>
        </div>
        <span className="subtle-tag">
          <Icon name="history" size={14} />
          {sample ? "2 illustrative amendments" : "Document comparison pending"}
        </span>
      </div>
      <div className="inline-notice">
        <Icon name="link" size={18} />
        <p>
          {sample
            ? "These synthetic amendment pairs demonstrate the review journey. They are not live changes to actual tenders."
            : "Live discovery preserves amendment links. PDF versioning and automatic condition comparison are the next backend milestone."}
        </p>
      </div>
      <div className="amendment-feed">
        {sample
          ? SAMPLE_CHANGES.map((change) => {
              const tender = tenders.find(
                (item) => item.id === change.tenderId,
              )!;
              return (
                <article className="amendment-feed-card" key={change.id}>
                  <div className="amendment-feed-top">
                    <span className="amendment-icon">
                      <Icon
                        name={change.type === "deadline" ? "clock" : "shield"}
                        size={22}
                      />
                    </span>
                    <div>
                      <span className="eyebrow">
                        {change.date} · SYNTHETIC SAMPLE
                      </span>
                      <h2>{change.field}</h2>
                      <button
                        className="text-link"
                        onClick={() => setSelected(tender)}
                      >
                        {tender.title}
                        <Icon name="arrow" size={14} />
                      </button>
                    </div>
                  </div>
                  <div className="before-after">
                    <div>
                      <small>PREVIOUS REQUIREMENT</small>
                      <span>{change.before}</span>
                    </div>
                    <Icon name="arrowRight" size={20} />
                    <div>
                      <small>UPDATED REQUIREMENT</small>
                      <strong>{change.after}</strong>
                    </div>
                  </div>
                  <p>{change.detail}</p>
                  <footer>
                    <span>
                      <Icon name="document" size={14} />
                      {change.clause} · illustrative evidence
                    </span>
                    <button
                      className="text-link"
                      onClick={() => setSelected(tender)}
                    >
                      Review tender <Icon name="arrowRight" size={15} />
                    </button>
                  </footer>
                </article>
              );
            })
          : tenders
              .filter((tender) => tender.amendmentUrls.length)
              .map((tender) => (
                <article className="amendment-feed-card" key={tender.id}>
                  <h2>{tender.title}</h2>
                  <p>Visible amendment links · not yet compared</p>
                  {tender.amendmentUrls.map((url, index) => (
                    <a
                      key={url}
                      className="document-card"
                      href={url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Amendment {index + 1}
                      <Icon name="arrow" size={15} />
                    </a>
                  ))}
                </article>
              ))}
      </div>
      {!sample && !tenders.some((tender) => tender.amendmentUrls.length) && (
        <div className="empty-state">
          <Icon name="history" size={34} />
          <h3>No amendment links in this discovery.</h3>
          <p>
            A bounded discovery result does not guarantee that no other
            amendments exist.
          </p>
        </div>
      )}
      {selected && (
        <TenderDrawer tender={selected} onClose={() => setSelected(null)} />
      )}
    </>
  );
}
