import type { SupplierProfile } from "./types";
import type { CertificateVerification } from "./certificate-types";

export function normalizedHolder(value: string) {
  return value
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]/gu, "");
}

export function hasVerifiedDocument(
  record: CertificateVerification,
  profile: Pick<SupplierProfile, "company" | "contact">,
  now = new Date(),
) {
  const subject = record.kind === "gst" ? profile.company : profile.contact;
  return (
    record.status === "verified" &&
    record.environment === "live" &&
    record.provider ===
      (record.kind === "gst" ? "entitylocker" : "digilocker") &&
    Boolean(normalizedHolder(subject)) &&
    normalizedHolder(record.subjectName) === normalizedHolder(subject) &&
    record.verifiedAt !== null &&
    Date.parse(record.verifiedAt) <= now.getTime() &&
    record.validUntil !== null &&
    Date.parse(record.validUntil) > now.getTime()
  );
}
