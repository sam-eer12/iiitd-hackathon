"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useEffect,
  useState,
  useSyncExternalStore,
} from "react";
import { hasVerifiedDocument } from "@/lib/certificate-verification";
import { useCertificateVerification } from "@/lib/use-certificate-verification";
import { useAuth } from "@/lib/auth-context";
import { auth } from "@/lib/firebase";
import { DEFAULT_PROFILE } from "@/lib/demo-data";
import { INITIAL_TENDER_CATALOG } from "@/lib/tender-catalog";
import {
  restoreWorkspace,
  type StoredWorkspace,
} from "@/lib/workspace-storage";
import type {
  DiscoveryJob,
  SupplierProfile,
  Tender,
  TenderCatalog,
} from "@/lib/types";

const STORAGE_KEY = "tenderlens.workspace.v1";
const initial: StoredWorkspace = {
  profile: DEFAULT_PROFILE,
  savedIds: [],
  liveTenders: INITIAL_TENDER_CATALOG.tenders,
  catalogRetrievedAt: INITIAL_TENDER_CATALOG.retrievedAt,
  job: null,
  collapsed: false,
};
const readySubscribe = () => () => {};

function readStoredWorkspace(key: string): StoredWorkspace {
  try {
    const raw = localStorage.getItem(key);
    return raw ? restoreWorkspace(JSON.parse(raw), initial) : initial;
  } catch {
    return initial;
  }
}

interface WorkspaceContextValue extends StoredWorkspace {
  certificateVerification: ReturnType<typeof useCertificateVerification>;
  verifiedCertificates: readonly (keyof SupplierProfile["certificates"])[];
  ready: boolean;
  tenders: Tender[];
  toast: string;
  discoveryError: string;
  evaluationTime: string;
  saveProfile: (profile: SupplierProfile) => void;
  toggleSaved: (id: string) => void;
  toggleSidebar: () => void;
  notify: (message: string) => void;
  refresh: (accessToken?: string) => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  return (
    <WorkspaceStateProvider
      key={loading ? "loading" : (user?.uid ?? "anonymous")}
    >
      {children}
    </WorkspaceStateProvider>
  );
}

function WorkspaceStateProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const storageKey = user ? `${STORAGE_KEY}.${user.uid}` : STORAGE_KEY;
  const [profileLoaded, setProfileLoaded] = useState(!user);
  const certificateVerification = useCertificateVerification();
  const ready = useSyncExternalStore(
    readySubscribe,
    () => true,
    () => false,
  );
  const [stored, setStored] = useState<StoredWorkspace>(initial);
  const [toast, setToast] = useState("");
  const [discoveryError, setDiscoveryError] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [evaluationTime, setEvaluationTime] = useState(
    INITIAL_TENDER_CATALOG.retrievedAt,
  );

  useEffect(() => {
    const workspace = readStoredWorkspace(storageKey);
    const timer = setTimeout(() => {
      setStored(workspace);
      setLoaded(true);
    }, 0);
    return () => clearTimeout(timer);
  }, [storageKey]);

  useEffect(() => {
    if (!loaded) return;
    const controller = new AbortController();
    fetch("/api/tenders", { signal: controller.signal, cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error("Source snapshot unavailable");
        const catalog: TenderCatalog = await response.json();
        setStored((previous) =>
          Date.parse(catalog.retrievedAt) >
          Date.parse(previous.catalogRetrievedAt)
            ? {
                ...previous,
                liveTenders: catalog.tenders,
                catalogRetrievedAt: catalog.retrievedAt,
              }
            : previous,
        );
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setDiscoveryError(
            "Could not load the latest source snapshot. Showing the last collected notices.",
          );
      });
    return () => controller.abort();
  }, [loaded]);

  useEffect(() => {
    if (loaded) {
      try {
        localStorage.setItem(storageKey, JSON.stringify(stored));
      } catch {
        /* Browser storage can be unavailable in private contexts. */
      }
    }
  }, [stored, loaded, storageKey]);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 4000);
    return () => clearTimeout(timer);
  }, [toast]);
  useEffect(() => {
    const update = () => setEvaluationTime(new Date().toISOString());
    const initialTimer = setTimeout(update, 0);
    const timer = setInterval(update, 60000);
    return () => {
      clearTimeout(initialTimer);
      clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    if (!user || !loaded) return;
    const controller = new AbortController();
    void user
      .getIdToken()
      .then(async (token) => {
        const response = await fetch("/api/profile", {
          headers: { Authorization: `Bearer ${token}` },
          cache: "no-store",
          signal: controller.signal,
        });
        if (response.ok) {
          const value = await response.json();
          if (!controller.signal.aborted && auth.currentUser?.uid === user.uid)
            setStored((previous) => ({
              ...previous,
              profile: {
                ...value.facts,
                turnover: value.facts.turnover.length
                  ? value.facts.turnover
                  : DEFAULT_PROFILE.turnover.map(({ year }) => ({
                      year,
                      amount: null,
                    })),
              },
            }));
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!controller.signal.aborted) setProfileLoaded(true);
      });
    return () => controller.abort();
  }, [user, loaded]);

  const applyJob = useCallback((job: DiscoveryJob) => {
    setStored((previous) => {
      const newer =
        job.status === "completed" &&
        Date.parse(job.finishedAt ?? job.createdAt) >=
          Date.parse(previous.catalogRetrievedAt);
      return {
        ...previous,
        job,
        liveTenders: newer ? (job.tenders ?? []) : previous.liveTenders,
        catalogRetrievedAt: newer
          ? (job.finishedAt ?? job.createdAt)
          : previous.catalogRetrievedAt,
      };
    });
    if (["failed", "submission_unknown", "cancelled"].includes(job.status))
      setDiscoveryError(
        job.error ??
          "Discovery could not finish. Your previous results are preserved.",
      );
  }, []);

  const jobId = stored.job?.id;
  const jobStatus = stored.job?.status;
  useEffect(() => {
    if (!jobId || !jobStatus || !["running", "submitting"].includes(jobStatus))
      return;
    const controller = new AbortController();
    const poll = async () => {
      try {
        const token = await auth.currentUser?.getIdToken();
        const response = await fetch(`/api/discovery/${jobId}`, {
          signal: controller.signal,
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        const payload = await response.json();
        if (response.ok) applyJob(payload.job);
        else if (!controller.signal.aborted)
          setDiscoveryError(
            payload.error ?? "Could not check this run. Try again shortly.",
          );
      } catch (error) {
        if (!(error instanceof DOMException && error.name === "AbortError"))
          setDiscoveryError(
            "Connection interrupted. The source run may still be active.",
          );
      }
    };
    const timer = setInterval(poll, 5000);
    void poll();
    return () => {
      controller.abort();
      clearInterval(timer);
    };
  }, [jobId, jobStatus, applyJob]);

  async function refresh(accessToken?: string) {
    setDiscoveryError("");
    try {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch("/api/discovery", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...(accessToken ? { "x-discovery-token": accessToken } : {}),
        },
        body: "{}",
      });
      const payload = await response.json();
      if (!response.ok) {
        setDiscoveryError(payload.error ?? "Could not start discovery.");
        return;
      }
      applyJob(payload.job);
      if (payload.job.status === "running")
        setToast(
          "TinyFish is checking the public source. You can continue reviewing your workspace.",
        );
    } catch {
      setDiscoveryError(
        "Could not reach discovery. Please check that the app server is running.",
      );
    }
  }

  const verifiedCertificates = useMemo(
    () =>
      certificateVerification.records
        .filter(
          (record) =>
            record.kind === "gst" &&
            hasVerifiedDocument(
              record,
              stored.profile,
              new Date(evaluationTime),
            ),
        )
        .map(() => "gst" as const),
    [certificateVerification.records, stored.profile, evaluationTime],
  );

  const value: WorkspaceContextValue = {
    ...stored,
    certificateVerification,
    verifiedCertificates,
    ready: ready && loaded && profileLoaded,
    tenders: stored.liveTenders,
    toast,
    discoveryError,
    evaluationTime,
    saveProfile: async (profile) => {
      setStored((previous) => ({ ...previous, profile }));
      const account = auth.currentUser;
      if (account) {
        try {
          const token = await account.getIdToken();
          const response = await fetch("/api/profile", {
            method: "PUT",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              facts: profile,
              provenance: "self-reported",
            }),
          });
          if (!response.ok) throw new Error("Save failed");
          setToast(
            "Supplier profile saved. Readiness checks have been updated.",
          );
        } catch {
          setToast(
            "Saved in this browser. Account storage is unavailable; please save again when connected.",
          );
        }
      } else
        setToast(
          "Supplier profile saved in this browser. Sign in to save it to your account.",
        );
    },
    toggleSaved: (id) =>
      setStored((previous) => ({
        ...previous,
        savedIds: previous.savedIds.includes(id)
          ? previous.savedIds.filter((saved) => saved !== id)
          : [...previous.savedIds, id],
      })),
    toggleSidebar: () =>
      setStored((previous) => ({
        ...previous,
        collapsed: !previous.collapsed,
      })),
    notify: setToast,
    refresh,
  };

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
      <div className={`toast ${toast ? "toast-visible" : ""}`} role="status">
        {toast}
      </div>
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context)
    throw new Error(
      "Workspace components must be used within WorkspaceProvider.",
    );
  return context;
}
