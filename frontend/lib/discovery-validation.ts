import type { Tender } from "./types";

const SOURCE_HOSTS = new Set(["iiitd.ac.in", "www.iiitd.ac.in"]);
export function validateSourceUrl(value: unknown): string {
  if (typeof value !== "string")
    throw new Error("A source URL is missing or invalid.");
  const url = new URL(value);
  if (
    url.protocol !== "https:" ||
    url.username ||
    url.password ||
    url.port ||
    !SOURCE_HOSTS.has(url.hostname)
  )
    throw new Error(
      "Discovery returned a URL outside the approved IIIT-Delhi source hosts.",
    );
  return url.href;
}

export function validateDiscoveryResult(
  result: unknown,
  retrievedAt: string,
  runId: string,
): Tender[] {
  if (!result || typeof result !== "object")
    throw new Error("The source run did not return a structured result.");
  const data = result as Record<string, unknown>;
  if (!["success", "no_matches", "failed"].includes(String(data.outcome)))
    throw new Error("The source result has an invalid outcome.");
  if (data.failure_reason !== null && typeof data.failure_reason !== "string")
    throw new Error("The source result has an invalid failure reason.");
  if (data.outcome === "failed")
    throw new Error(
      "TinyFish could not inspect the public notice content. Your previous workspace has been preserved.",
    );
  if (!Array.isArray(data.notices) || data.notices.length > 5)
    throw new Error("The source result must contain at most five notices.");
  if (data.outcome === "no_matches" && data.notices.length)
    throw new Error("A no-matches result must contain an empty notice list.");
  if (data.outcome === "success" && !data.notices.length)
    throw new Error("The source returned success without any notices.");
  const seen = new Set<string>();
  return data.notices.map((value, index) => {
    if (!value || typeof value !== "object")
      throw new Error("A notice is not a valid object.");
    const notice = value as Record<string, unknown>;
    if (
      typeof notice.title !== "string" ||
      !notice.title.trim() ||
      notice.title.length > 500
    )
      throw new Error("A notice title is missing or invalid.");
    if (notice.notice_id !== null && typeof notice.notice_id !== "string")
      throw new Error("A notice reference is invalid.");
    if (
      notice.deadline_text !== null &&
      typeof notice.deadline_text !== "string"
    )
      throw new Error("A notice deadline is invalid.");
    if (
      !Array.isArray(notice.pdf_urls) ||
      !Array.isArray(notice.amendment_urls)
    )
      throw new Error("A notice document list is invalid.");
    const sourceUrl = validateSourceUrl(notice.source_url);
    const pdfUrls = [...new Set(notice.pdf_urls.map(validateSourceUrl))];
    const amendmentUrls = [
      ...new Set(notice.amendment_urls.map(validateSourceUrl)),
    ];
    const identity = `${notice.notice_id ?? ""}|${notice.title}|${sourceUrl}`;
    if (seen.has(identity))
      throw new Error("The source returned duplicate notice entries.");
    seen.add(identity);
    return {
      id: `live-${runId}-${index}`,
      reference:
        typeof notice.notice_id === "string" && notice.notice_id.trim()
          ? notice.notice_id
          : "Reference not provided",
      title: notice.title.trim(),
      description:
        "Discovered on the public source. PDF clause verification is pending.",
      issuer: "IIIT-Delhi",
      category: "Unclassified",
      value: "Not extracted",
      deadlineText: notice.deadline_text as string | null,
      deadline: null,
      relevance: null,
      sourceUrl,
      pdfUrls,
      amendmentUrls,
      provenance: "live",
      retrievedAt,
      amended: amendmentUrls.length > 0,
      conditions: [],
    };
  });
}
