"use client";

import { useState } from "react";
import { Icon } from "./icon";
import { useWorkspace } from "./workspace-provider";
import { hasVerifiedDocument } from "@/lib/certificate-verification";
import type { SupplierProfile } from "@/lib/types";
import type { VerificationKind } from "@/lib/certificate-types";

export function ProfileVerificationBadges({
  profile,
}: {
  profile: SupplierProfile;
}) {
  const { certificateVerification, evaluationTime } = useWorkspace();
  const verified = certificateVerification.records.filter((record) =>
    hasVerifiedDocument(record, profile, new Date(evaluationTime)),
  );
  return (
    <>
      {(["gst", "pan"] as const).map((kind) =>
        verified.find((record) => record.kind === kind) ? (
          <span className="verified-document-tag" key={kind}>
            <Icon name="shield" size={14} />
            {kind === "gst"
              ? "GST verified by EntityLocker"
              : "PAN verified by DigiLocker"}
          </span>
        ) : null,
      )}
    </>
  );
}

export function CertificateDeclarationNote({
  kind,
  profile,
}: {
  kind: keyof SupplierProfile["certificates"];
  profile: SupplierProfile;
}) {
  const { certificateVerification, evaluationTime } = useWorkspace();
  const verified =
    kind === "gst" &&
    certificateVerification.records.some(
      (record) =>
        record.kind === "gst" &&
        hasVerifiedDocument(record, profile, new Date(evaluationTime)),
    );
  return (
    <small className="certificate-declaration">
      {verified
        ? "GST document verified by EntityLocker"
        : "Self-declared · document not verified"}
    </small>
  );
}

const statusLabels = {
  submitting: "Starting verification",
  submission_unknown: "Session needs review",
  pending: "Waiting for document consent",
  cancelled: "Session stopped",
  verified: "Issuer document verified",
  test_passed: "Test check passed",
  review: "Review needed",
  failed: "Check unsuccessful",
  expired: "Verification expired",
};

export function CertificateVerificationPanel({
  profile,
  dirty,
}: {
  profile: SupplierProfile;
  dirty: boolean;
}) {
  const { certificateVerification: verification, evaluationTime } =
    useWorkspace();
  const [kind, setKind] = useState<VerificationKind>("gst");
  const [number, setNumber] = useState("");
  const [consent, setConsent] = useState(false);
  const [flow, setFlow] = useState<"signin" | "signup">("signin");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const subjectName = kind === "gst" ? profile.company : profile.contact;
  const provider = kind === "gst" ? "EntityLocker" : "DigiLocker";
  const latest = verification.records.find((record) => record.kind === kind);
  const verified =
    latest && hasVerifiedDocument(latest, profile, new Date(evaluationTime));

  async function start() {
    setError("");
    const pattern =
      kind === "gst"
        ? /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$/
        : /^[A-Z]{5}[0-9]{4}[A-Z]$/;
    if (dirty) {
      setError("Save your profile changes before continuing.");
      return;
    }
    if (!pattern.test(number.trim().toUpperCase())) {
      setError(
        kind === "pan"
          ? "Enter your PAN as 5 letters, 4 digits, then 1 letter (for example, ABCDE1234F)."
          : "Enter a valid 15-character GSTIN as printed on your GST registration.",
      );
      return;
    }
    if (subjectName.trim().length < 2) {
      setError(
        kind === "pan"
          ? "Set Contact person to your full name as printed on your PAN, then save your profile."
          : "Enter the registered business name in your profile, then save it.",
      );
      return;
    }
    if (!consent) {
      setError("Give consent to share this document before continuing.");
      return;
    }
    setBusy(true);
    try {
      const result = await verification.start(
        kind,
        subjectName,
        number.trim().toUpperCase(),
        consent,
        flow,
      );
      setNumber("");
      setConsent(false);
      if (result.authorizationUrl)
        window.location.assign(result.authorizationUrl);
      else await verification.refresh();
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Document verification could not start.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function restart() {
    if (!latest) return;
    setBusy(true);
    setError("");
    try {
      const response = await verification.restart(latest.id, flow);
      if (response.authorizationUrl)
        window.location.assign(response.authorizationUrl);
      else await verification.refresh();
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "The OAuth session could not be restarted.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="certificate-verification-panel" id="document-verification">
      <div className="verification-intro">
        <Icon name="shield" size={21} />
        <div>
          <h3>Back your profile with issuer evidence.</h3>
          <p>
            Self-declared certificates stay unverified. Connect your locker to
            confirm the document’s issuer, signature, and holder.
          </p>
        </div>
      </div>
      <p className="verification-scope">
        GST registration uses EntityLocker. DigiLocker can verify the contact
        person’s PAN; it does not verify the business’s other certificates. ISO
        9001 and manufacturer authorization still need an issuer check.
      </p>
      {!verification.signedIn ? (
        <button
          type="button"
          className="button button-secondary button-small"
          disabled={verification.loading || busy}
          onClick={() => {
            setBusy(true);
            void verification
              .signInWithGoogle()
              .catch(() => setError("Sign-in could not finish. Try again."))
              .finally(() => setBusy(false));
          }}
        >
          <Icon name="shield" size={15} /> Sign in to verify documents
        </button>
      ) : (
        <>
          <div className="verification-fields">
            <label>
              Document to verify
              <select
                value={kind}
                disabled={busy}
                onChange={(event) => {
                  setKind(event.target.value as VerificationKind);
                  setNumber("");
                  setConsent(false);
                  setError("");
                }}
              >
                <option value="gst">GST registration · EntityLocker</option>
                <option value="pan">Contact person’s PAN · DigiLocker</option>
              </select>
            </label>
            <label>
              {kind === "gst" ? "GSTIN" : "PAN number"}
              <input
                autoComplete="off"
                spellCheck={false}
                maxLength={kind === "gst" ? 15 : 10}
                value={number}
                onChange={(event) => {
                  setNumber(event.target.value.toUpperCase());
                  setError("");
                }}
                placeholder={
                  kind === "gst" ? "15-character GSTIN" : "ABCDE1234F (example)"
                }
                disabled={busy}
              />
              {kind === "pan" && (
                <small>Format: 5 letters, 4 digits, then 1 letter.</small>
              )}
            </label>
            <label>
              {provider} account
              <select
                value={flow}
                onChange={(event) =>
                  setFlow(event.target.value as "signin" | "signup")
                }
                disabled={busy}
              >
                <option value="signin">I already have an account</option>
                <option value="signup">
                  Create an account during verification
                </option>
              </select>
            </label>
          </div>
          <p className="verification-holder">
            The document must be issued to{" "}
            <strong>{subjectName || "the name in your saved profile"}</strong>.
          </p>
          <label className="verification-consent">
            <input
              type="checkbox"
              checked={consent}
              onChange={(event) => setConsent(event.target.checked)}
              disabled={busy}
            />
            <span>
              I authorize TenderLens to retrieve this issuer document through
              Sandbox and {provider}, check its signature and holder details
              {kind === "gst"
                ? ", and confirm the GST registration is active"
                : ""}
              .{" "}
              {kind === "gst"
                ? "I am authorized to act for this business."
                : "This is my own PAN document."}
            </span>
          </label>
          <div className="verification-actions">
            <button
              type="button"
              className="button button-primary button-small"
              onClick={() => void start()}
              disabled={
                busy ||
                dirty ||
                !consent ||
                !number.trim() ||
                !verification.availableKinds.includes(kind)
              }
            >
              <Icon
                name={busy ? "refresh" : "shield"}
                size={15}
                className={busy ? "spin" : ""}
              />
              {busy ? "Checking…" : `Continue to ${provider}`}
            </button>
            <button
              type="button"
              className="text-link"
              disabled={busy}
              onClick={() => void verification.refresh()}
            >
              Refresh verification status
            </button>
          </div>
          {dirty && (
            <p className="verification-note">
              Save your profile changes before starting a document check.
            </p>
          )}
          {!verification.availableKinds.includes(kind) &&
            !verification.error && (
              <p className="verification-note">
                Document verification is not available yet. Your declarations
                remain unverified.
              </p>
            )}
          {verification.configured && verification.environment === "test" && (
            <p className="verification-note">
              Test mode: checks cannot award a live verification badge.
            </p>
          )}
        </>
      )}
      {latest && (
        <div
          className={`verification-receipt ${verified ? "is-verified" : ""}`}
          role="status"
        >
          <div>
            <strong>
              {verified
                ? `Verified by ${provider}`
                : latest.status === "verified"
                  ? "Verify again for the current profile"
                  : statusLabels[latest.status]}
            </strong>
            <p>
              {latest.subjectName} · {latest.maskedNumber}
            </p>
            <p>{latest.message}</p>
            {latest.issuer && <small>Issuer: {latest.issuer}</small>}
            {latest.verifiedAt && (
              <small>
                Checked{" "}
                {new Date(latest.verifiedAt).toLocaleString("en-GB", {
                  timeZone: "Asia/Kolkata",
                })}{" "}
                IST
              </small>
            )}
          </div>
          {latest.status === "pending" && (
            <button
              type="button"
              className="button button-secondary button-small"
              disabled={busy}
              onClick={() => void restart()}
              title={`Stop this session and restart ${provider} sign-in`}
            >
              {busy ? "Restarting…" : "Check again"}
            </button>
          )}
        </div>
      )}
      {(error || verification.error) && (
        <p className="verification-error" role="alert">
          {error || verification.error}
        </p>
      )}
    </div>
  );
}
