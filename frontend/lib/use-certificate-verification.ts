"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "./auth-context";
import type {
  CertificateVerification,
  CertificateVerificationList,
  StartVerificationResponse,
  VerificationKind,
} from "./certificate-types";

export function useCertificateVerification() {
  const { user, loading, signInWithGoogle } = useAuth();
  const [state, setState] = useState<{
    owner: string;
    data: CertificateVerificationList | null;
    error: string;
  } | null>(null);
  // Receipts are never read from or written to localStorage. A different account
  // cannot inherit the previous user's badges while its request is loading.
  const current = state?.owner === user?.uid ? state : null;
  const records = current?.data?.verifications ?? [];

  const request = useCallback(
    async <T>(path: string, init?: RequestInit): Promise<T> => {
      if (!user) throw new Error("Sign in to verify your documents.");
      const token = await user.getIdToken();
      const response = await fetch(`/api/certificates${path}`, {
        ...init,
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        cache: "no-store",
      });
      const payload = await response.json();
      if (!response.ok)
        throw new Error(
          typeof payload.error?.message === "string"
            ? payload.error.message
            : "The document check could not be completed.",
        );
      return payload;
    },
    [user],
  );

  const refresh = useCallback(
    async (signal?: AbortSignal) => {
      if (!user) return;
      try {
        const data = await request<CertificateVerificationList>("", { signal });
        if (!signal?.aborted) setState({ owner: user.uid, data, error: "" });
      } catch (error) {
        if (!signal?.aborted)
          setState((previous) => ({
            owner: user.uid,
            data: previous?.owner === user.uid ? previous.data : null,
            error:
              error instanceof Error
                ? error.message
                : "Document verification is unavailable.",
          }));
      }
    },
    [request, user],
  );

  useEffect(() => {
    if (!user) return;
    const controller = new AbortController();
    void refresh(controller.signal);
    return () => controller.abort();
  }, [refresh, user]);

  const remember = useCallback(
    (record: CertificateVerification) => {
      if (!user) return;
      setState((previous) => {
        if (previous?.owner !== user.uid || !previous.data) return previous;
        return {
          ...previous,
          error: "",
          data: {
            ...previous.data,
            verifications: [
              record,
              ...previous.data.verifications.filter(
                (item) => item.id !== record.id,
              ),
            ],
          },
        };
      });
    },
    [user],
  );

  const check = useCallback(
    async (id: string) => {
      const record = await request<CertificateVerification>(`/${id}/check`, {
        method: "POST",
        body: "{}",
      });
      remember(record);
      return record;
    },
    [remember, request],
  );

  const pending = records
    .filter((record) => record.status === "pending")
    .map((record) => record.id)
    .join(",");
  useEffect(() => {
    if (!pending) return;
    let attempts = 0;
    const poll = () => {
      if (document.visibilityState !== "visible") return;
      if (++attempts > 75) {
        clearInterval(timer);
        return;
      }
      for (const id of pending.split(",")) void check(id).catch(() => {});
    };
    const timer = setInterval(poll, 8000);
    poll();
    return () => clearInterval(timer);
  }, [pending, check]);

  async function start(
    kind: VerificationKind,
    subjectName: string,
    documentNumber: string,
    consent: boolean,
    flow: "signin" | "signup",
  ) {
    const response = await request<StartVerificationResponse>("", {
      method: "POST",
      body: JSON.stringify({
        kind,
        subjectName,
        documentNumber,
        consent,
        requestKey: crypto.randomUUID(),
        flow,
      }),
    });
    remember(response.verification);
    return response;
  }

  return {
    records,
    configured: current?.data?.configured ?? false,
    availableKinds: current?.data?.availableKinds ?? [],
    environment: current?.data?.environment ?? "test",
    error: current?.error ?? "",
    signedIn: Boolean(user),
    loading,
    signInWithGoogle,
    refresh,
    check,
    start,
  };
}
