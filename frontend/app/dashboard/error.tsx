"use client";

import { ErrorState } from "@/components/error-state";

/* Keeps the dashboard shell (sidebar and top bar) around the error. */
export default function DashboardError({
  error,
  retry,
}: {
  error: unknown;
  retry: () => void;
}) {
  return (
    <ErrorState
      error={error}
      retry={retry}
      homeHref="/dashboard"
      homeLabel="Back to overview"
    />
  );
}
