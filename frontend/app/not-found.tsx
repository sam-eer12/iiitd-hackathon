import type { Metadata } from "next";
import Link from "next/link";
import { Icon } from "@/components/icon";
import { SiteHeader } from "@/components/site-header";
import { StatePanel } from "@/components/state-panel";

export const metadata: Metadata = { title: "Page not found" };

export default function NotFound() {
  return (
    <div className="landing state-page">
      <SiteHeader />
      <main className="page-width">
        <StatePanel
          icon="search"
          eyebrow="404"
          title="This page could not be found."
          actions={
            <>
              <Link className="button button-primary" href="/dashboard">
                Open workspace <Icon name="arrowRight" size={16} />
              </Link>
              <Link className="button button-secondary" href="/">
                Back to home
              </Link>
            </>
          }
        >
          The link may be outdated, or the notice or document no longer exists.
          Your workspace and saved tenders are unaffected.
        </StatePanel>
      </main>
    </div>
  );
}
