export type Readiness = "meets" | "review" | "blocked";
export type ConditionType =
  "turnover" | "experience" | "certificate" | "deposit" | "deadline";

export interface SupplierProfile {
  company: string;
  contact: string;
  email: string;
  categories: string[];
  turnover: { year: string; amount: number | null }[];
  completedOrders: number | null;
  depositCapacity: number | null;
  certificates: {
    gst: boolean | null;
    iso: boolean | null;
    manufacturer: boolean | null;
  };
}

export interface Condition {
  type: ConditionType;
  label: string;
  requirement: string;
  quote: string;
  page: number;
  clause: string;
  threshold?: number;
  years?: string[];
  certificate?: keyof SupplierProfile["certificates"];
  deadline?: string;
}

export interface Tender {
  id: string;
  reference: string;
  title: string;
  description: string;
  issuer: string;
  category: string;
  value: string;
  deadlineText: string | null;
  deadline: string | null;
  relevance: number | null;
  sourceUrl: string;
  pdfUrls: string[];
  amendmentUrls: string[];
  provenance: "sample" | "live";
  retrievedAt: string;
  amended: boolean;
  conditions: Condition[];
}

export interface Finding {
  condition: Condition;
  status: Readiness;
  reason: string;
  supplierValue: string;
}
export interface Evaluation {
  status: Readiness;
  findings: Finding[];
  coverageComplete: boolean;
}

export interface DiscoveryJob {
  id: string;
  providerRunId: string | null;
  status:
    | "submitting"
    | "submission_unknown"
    | "running"
    | "completed"
    | "failed"
    | "cancelled";
  createdAt: string;
  finishedAt?: string;
  error?: string;
  tenders?: Tender[];
}
