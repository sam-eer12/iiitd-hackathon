import snapshot from "./data/iiitd-tenders.json";
import { validateDiscoveryResult } from "./discovery-validation";
import type { TenderCatalog } from "./types";

// A recorded TinyFish response from the official source, with no invented clauses.
// New completed application runs replace this snapshot through /api/tenders.
export const INITIAL_TENDER_CATALOG: TenderCatalog = {
  tenders: validateDiscoveryResult(
    snapshot.result,
    snapshot.retrievedAt,
    snapshot.providerRunId,
  ),
  retrievedAt: snapshot.retrievedAt,
  providerRunId: snapshot.providerRunId,
  sourceUrl: snapshot.sourceUrl,
};
