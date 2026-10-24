import { tenderIdentity, validateSourceUrl } from "./discovery-validation.ts";
import type { DiscoveryJob, SupplierProfile, Tender } from "./types";

export interface StoredWorkspace {
  profile: SupplierProfile;
  savedIds: string[];
  liveTenders: Tender[];
  catalogRetrievedAt: string;
  job: DiscoveryJob | null;
  collapsed: boolean;
}

export function restoreWorkspace(
  value: unknown,
  initial: StoredWorkspace,
): StoredWorkspace {
  try {
    if (!value || typeof value !== "object") return initial;
    const stored = value as StoredWorkspace;
    if (
      !stored.profile?.turnover ||
      !Array.isArray(stored.savedIds) ||
      !Array.isArray(stored.liveTenders)
    )
      return initial;
    const previousTenders = stored.liveTenders.filter(
      (tender) => tender.provenance === "live",
    );
    for (const tender of previousTenders) {
      validateSourceUrl(tender.sourceUrl);
      [...tender.pdfUrls, ...tender.amendmentUrls].forEach(validateSourceUrl);
    }
    const retrievedAt =
      stored.catalogRetrievedAt ??
      (stored.job?.status === "completed"
        ? stored.job.finishedAt
        : undefined) ??
      previousTenders
        .map((tender) => tender.retrievedAt)
        .sort()
        .at(-1) ??
      "";
    const keepCached =
      Date.parse(retrievedAt) > Date.parse(initial.catalogRetrievedAt);
    return {
      profile: stored.profile,
      savedIds: stored.savedIds
        .filter((id) => !id.startsWith("sample-"))
        .map((id) => {
          const tender = previousTenders.find((item) => item.id === id);
          return tender ? tenderIdentity(tender) : id;
        }),
      liveTenders: keepCached
        ? previousTenders.map((tender) => ({
            ...tender,
            id: tenderIdentity(tender),
          }))
        : initial.liveTenders,
      catalogRetrievedAt: keepCached ? retrievedAt : initial.catalogRetrievedAt,
      job: stored.job ?? null,
      collapsed: stored.collapsed === true,
    };
  } catch {
    return initial;
  }
}
