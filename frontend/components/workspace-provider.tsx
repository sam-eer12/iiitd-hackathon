"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  useSyncExternalStore,
} from "react";
import { DEFAULT_PROFILE, DEMO_CLOCK, SAMPLE_TENDERS } from "@/lib/demo-data";
import type { DiscoveryJob, SupplierProfile, Tender } from "@/lib/types";

const STORAGE_KEY = "tenderlens.workspace.v1";
interface StoredWorkspace {
  profile: SupplierProfile;
  savedIds: string[];
  liveTenders: Tender[];
  collectionMode: "sample" | "live";
  job: DiscoveryJob | null;
  collapsed: boolean;
}
const initial: StoredWorkspace = {
  profile: DEFAULT_PROFILE,
  savedIds: ["sample-1", "sample-2"],
  liveTenders: [],
  collectionMode: "sample",
  job: null,
  collapsed: false,
};
const readySubscribe = () => () => {};

function readStoredWorkspace(): StoredWorkspace {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return initial;
    const value = JSON.parse(raw);
    if (
      !value.profile?.turnover ||
      !Array.isArray(value.savedIds) ||
      !Array.isArray(value.liveTenders)
    )
      return initial;
    return { ...initial, ...value };
  } catch {
    return initial;
  }
}

interface WorkspaceContextValue extends StoredWorkspace {
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
  clearLiveResults: () => void;
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const ready = useSyncExternalStore(
    readySubscribe,
    () => true,
    () => false,
  );
  const [stored, setStored] = useState<StoredWorkspace>(initial);
  const [toast, setToast] = useState("");
  const [discoveryError, setDiscoveryError] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [evaluationTime, setEvaluationTime] = useState(DEMO_CLOCK);

  useEffect(() => {
    const workspace = readStoredWorkspace();
    const timer = setTimeout(() => {
      setStored(workspace);
      setLoaded(true);
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (loaded) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
      } catch {
        /* Browser storage can be unavailable in private contexts. */
      }
    }
  }, [stored, loaded]);
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

  const applyJob = useCallback((job: DiscoveryJob) => {
    setStored((previous) => ({
      ...previous,
      job,
      collectionMode:
        job.status === "completed" ? "live" : previous.collectionMode,
      liveTenders:
        job.status === "completed" ? (job.tenders ?? []) : previous.liveTenders,
    }));
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
        const response = await fetch(`/api/discovery/${jobId}`, {
          signal: controller.signal,
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
      const response = await fetch("/api/discovery", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
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

  const value: WorkspaceContextValue = {
    ...stored,
    ready: ready && loaded,
    tenders:
      stored.collectionMode === "live" ? stored.liveTenders : SAMPLE_TENDERS,
    toast,
    discoveryError,
    evaluationTime,
    saveProfile: (profile) => {
      setStored((previous) => ({ ...previous, profile }));
      setToast("Supplier profile saved. Readiness checks have been updated.");
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
    clearLiveResults: () => {
      setStored((previous) => ({
        ...previous,
        liveTenders: [],
        job: null,
        collectionMode: "sample",
      }));
      setToast("Showing the illustrative sample workspace.");
    },
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
