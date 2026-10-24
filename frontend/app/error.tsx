"use client";

import { ErrorState } from "@/components/error-state";
import { SiteHeader } from "@/components/site-header";

export default function RootError({
  error,
  retry,
}: {
  error: unknown;
  retry: () => void;
}) {
  return (
    <div className="landing state-page">
      <SiteHeader />
      <main className="page-width">
        <ErrorState
          error={error}
          retry={retry}
          homeHref="/"
          homeLabel="Back to home"
        />
      </main>
    </div>
  );
}
