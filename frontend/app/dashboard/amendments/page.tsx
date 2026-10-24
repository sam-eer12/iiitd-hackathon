"use client";

import { Icon } from "@/components/icon";
import { useWorkspace } from "@/components/workspace-provider";

export default function AmendmentsPage() {
  const { tenders } = useWorkspace();
  const amended = tenders.filter((tender) => tender.amendmentUrls.length);
  return (
    <>
      <div className="workspace-heading">
        <div>
          <div className="eyebrow">EVERY CHANGE, IN SIGHT</div>
          <h1>A clearer view of what changed.</h1>
          <p>Amendment documents linked from the official source.</p>
        </div>
        <span className="subtle-tag">
          <Icon name="history" size={14} />
          Document comparison pending
        </span>
      </div>
      <div className="inline-notice">
        <Icon name="link" size={18} />
        <p>
          TinyFish preserves amendment links associated with each notice. Read
          the source documents to confirm what changed; automatic comparison is
          pending.
        </p>
      </div>
      <div className="amendment-feed">
        {amended.map((tender) => (
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
      {!amended.length && (
        <div className="empty-state">
          <Icon name="history" size={34} />
          <h3>No amendment links in this discovery.</h3>
          <p>
            A bounded discovery result does not guarantee that no other
            amendments exist.
          </p>
        </div>
      )}
    </>
  );
}
