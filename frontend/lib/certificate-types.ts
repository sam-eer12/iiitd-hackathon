export type VerificationKind = "gst" | "pan";

export interface CertificateVerification {
  id: string;
  kind: VerificationKind;
  provider: "entitylocker" | "digilocker";
  environment: "test" | "live";
  subjectName: string;
  maskedNumber: string;
  status:
    | "submitting"
    | "submission_unknown"
    | "pending"
    | "cancelled"
    | "verified"
    | "test_passed"
    | "review"
    | "failed"
    | "expired";
  message: string;
  issuer: string | null;
  createdAt: string;
  verifiedAt: string | null;
  validUntil: string | null;
}

export interface CertificateVerificationList {
  configured: boolean;
  availableKinds: VerificationKind[];
  environment: "test" | "live";
  verifications: CertificateVerification[];
}

export interface StartVerificationResponse {
  verification: CertificateVerification;
  authorizationUrl: string | null;
}
