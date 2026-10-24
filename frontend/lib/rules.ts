import type {
  Condition,
  Evaluation,
  Finding,
  SupplierProfile,
  Tender,
} from "./types";

export const STATUS_LABELS = {
  meets: "Meets checked conditions",
  review: "Review needed",
  blocked: "Blocked",
};
const money = (value: number) => `₹${value.toLocaleString("en-IN")}`;
const missing = (condition: Condition, reason: string): Finding => ({
  condition,
  status: "review",
  reason,
  supplierValue: "Not provided",
});

export function evaluateCondition(
  condition: Condition,
  profile: SupplierProfile,
  now: Date,
  verifiedCertificates: readonly (keyof SupplierProfile["certificates"])[] = [],
): Finding {
  if (
    !condition.quote ||
    !Number.isInteger(condition.page) ||
    condition.page < 1
  )
    return missing(
      condition,
      "The requirement needs a source clause and a valid page reference.",
    );
  if (condition.type === "turnover") {
    if (!condition.years?.length || condition.threshold === undefined)
      return missing(
        condition,
        "The exact turnover period or required amount is unresolved.",
      );
    const values = condition.years.map(
      (year) => profile.turnover.find((entry) => entry.year === year)?.amount,
    );
    if (
      values.some(
        (value) =>
          value === null ||
          value === undefined ||
          !Number.isFinite(value) ||
          value < 0,
      )
    )
      return missing(
        condition,
        "Add turnover for every requested financial year before comparing the average.",
      );
    const average =
      (values as number[]).reduce((total, value) => total + value, 0) /
      values.length;
    return {
      condition,
      status: average >= condition.threshold ? "meets" : "blocked",
      supplierValue: `${money(average)} average`,
      reason: `${condition.years.join(", ")}: your average ${average >= condition.threshold ? "meets" : "is below"} the required ${money(condition.threshold)}.`,
    };
  }
  if (condition.type === "experience" || condition.type === "deposit") {
    const value =
      condition.type === "experience"
        ? profile.completedOrders
        : profile.depositCapacity;
    if (
      value === null ||
      !Number.isFinite(value) ||
      value < 0 ||
      condition.threshold === undefined
    )
      return missing(
        condition,
        "Add a known supplier value and confirm the exact requirement.",
      );
    return {
      condition,
      status: value >= condition.threshold ? "meets" : "blocked",
      supplierValue:
        condition.type === "deposit"
          ? money(value)
          : `${value} completed orders`,
      reason:
        condition.type === "deposit"
          ? "Compares your stated available funds with the required EMD; this does not confirm payment."
          : "Compares the declared count of completed supply orders in this sample category.",
    };
  }
  if (condition.type === "certificate") {
    if (!condition.certificate)
      return missing(condition, "The certificate type is unresolved.");
    const value = profile.certificates[condition.certificate];
    if (value === null)
      return missing(
        condition,
        "Confirm whether you have this certificate. Unknown does not count as a pass.",
      );
    if (value && !verifiedCertificates.includes(condition.certificate))
      return {
        condition,
        status: "review",
        supplierValue: "Present · self-declared",
        reason:
          "The certificate is self-declared. An issuer verification is required before this check can pass.",
      };
    return {
      condition,
      status: value ? "meets" : "blocked",
      supplierValue: value ? "Issuer verified" : "Confirmed absent",
      reason: value
        ? "The certificate has a current issuer verification matching this supplier."
        : "Your profile confirms that the required certificate is absent.",
    };
  }
  if (!condition.deadline || !/(?:Z|[+-]\d{2}:\d{2})$/.test(condition.deadline))
    return missing(condition, "The deadline needs an exact time and timezone.");
  const deadline = new Date(condition.deadline);
  if (!Number.isFinite(deadline.getTime()) || !Number.isFinite(now.getTime()))
    return missing(
      condition,
      "A valid evaluation time and deadline are required.",
    );
  return {
    condition,
    status: now < deadline ? "meets" : "blocked",
    supplierValue:
      now < deadline ? "Open at evaluation time" : "Deadline passed",
    reason: `Checked against ${now.toLocaleString("en-GB", { timeZone: "Asia/Kolkata" })} IST.`,
  };
}

export function evaluateTender(
  tender: Tender,
  profile: SupplierProfile,
  now: Date,
  verifiedCertificates: readonly (keyof SupplierProfile["certificates"])[] = [],
): Evaluation {
  const findings = tender.conditions.map((condition) =>
    evaluateCondition(condition, profile, now, verifiedCertificates),
  );
  const coverageComplete =
    new Set(tender.conditions.map((condition) => condition.type)).size === 5;
  const status = findings.some((finding) => finding.status === "blocked")
    ? "blocked"
    : !coverageComplete ||
        findings.some((finding) => finding.status === "review")
      ? "review"
      : "meets";
  return { status, findings, coverageComplete };
}
