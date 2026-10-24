"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "./auth-context";
import { auth } from "./firebase";
import { sourceReviewVersion } from "./purchases";
import type { DemoPurchase } from "./purchases";
import type { Tender } from "./types";

export function useDemoPurchases() {
  const { user } = useAuth();
  const [orders, setOrders] = useState<DemoPurchase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const request = useCallback(
    async <T>(path: string, init?: RequestInit): Promise<T> => {
      if (!user)
        throw new Error("Sign in with Google to buy a tender in the demo.");
      const token = await user.getIdToken();
      const response = await fetch(`/api/purchases${path}`, {
        ...init,
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        cache: "no-store",
      });
      const payload = await response.json();
      if (auth.currentUser?.uid !== user.uid)
        throw new Error("Your account changed. Please reopen checkout.");
      if (!response.ok)
        throw new Error(
          payload.error?.message ??
            "Checkout is temporarily unavailable. Please try again.",
        );
      return payload;
    },
    [user],
  );

  const reload = useCallback(
    async (signal?: AbortSignal) => {
      if (!user) return;
      try {
        const result = await request<{ purchases: DemoPurchase[] }>("", {
          signal,
        });
        if (!signal?.aborted) {
          setOrders(result.purchases);
          setError("");
        }
      } catch (failure) {
        if (!signal?.aborted)
          setError(
            failure instanceof Error
              ? failure.message
              : "Could not load your demo purchases.",
          );
      } finally {
        if (!signal?.aborted) setLoading(false);
      }
    },
    [request, user],
  );

  useEffect(() => {
    const controller = new AbortController();
    void Promise.resolve().then(() => {
      if (!controller.signal.aborted) return reload(controller.signal);
    });
    return () => controller.abort();
  }, [reload]);

  const remember = (order: DemoPurchase) => {
    setOrders((previous) => [
      order,
      ...previous.filter((item) => item.id !== order.id),
    ]);
    setError("");
    return order;
  };

  return {
    orders: user ? orders : [],
    loading: !!user && loading,
    error: user ? error : "",
    reload,
    start: async (tender: Tender) =>
      remember(
        await request<DemoPurchase>("", {
          method: "POST",
          body: JSON.stringify({
            tenderId: tender.id,
            reviewVersion: sourceReviewVersion(tender),
            reviewed: true,
            demoAcknowledged: true,
          }),
        }),
      ),
    pay: async (id: string, outcome: "success" | "failure") =>
      remember(
        await request<DemoPurchase>(`/${id}/pay`, {
          method: "POST",
          body: JSON.stringify({ outcome }),
        }),
      ),
  };
}
