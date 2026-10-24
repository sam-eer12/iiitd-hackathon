"use client";

import Link from "next/link";
import { useEffect } from "react";
import { Icon } from "./icon";
import { StatePanel } from "./state-panel";

/* Shared fallback for app/error.tsx and app/dashboard/error.tsx. */
export function ErrorState({
  error,
  retry,
  homeHref,
  homeLabel,
}: {
  error: unknown;
  retry: () => void;
  homeHref: string;
  homeLabel: string;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);
  const digest =
    error instanceof Error && "digest" in error
      ? String((error as Error & { digest?: string }).digest ?? "")
      : "";
  return (
    <StatePanel
      icon="alert"
      eyebrow="Something went wrong"
      title="This view could not load."
      actions={
        <>
          <button
            type="button"
            className="button button-primary"
            onClick={() => retry()}
          >
            <Icon name="refresh" size={16} /> Try again
          </button>
          <Link className="button button-secondary" href={homeHref}>
            {homeLabel}
          </Link>
        </>
      }
    >
      An unexpected error interrupted this page. Your saved profile, bookmarks,
      and discovery records are kept.
      {digest && (
        <>
          {" "}
          Reference: <code>{digest}</code>
        </>
      )}
    </StatePanel>
  );
}
