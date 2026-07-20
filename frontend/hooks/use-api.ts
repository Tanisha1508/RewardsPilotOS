"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiRequestError } from "@/lib/api";

export interface LoadState<T> {
  data: T | null;
  error: { message: string; requestId?: string } | null;
  loading: boolean;
  reload: () => void;
}

/** Load data from the API, keeping "loading", "failed", and "loaded but empty"
 *  distinct. Collapsing them is how a UI ends up showing "No cards" when what
 *  actually happened was a 500. */
export function useApi<T>(fetcher: () => Promise<T>, deps: unknown[] = []): LoadState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<LoadState<T>["error"]>(null);
  const [loading, setLoading] = useState(true);
  const [nonce, setNonce] = useState(0);

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetcher()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((caught) => {
        if (cancelled) return;
        setData(null);
        setError(
          caught instanceof ApiRequestError
            ? { message: caught.message, requestId: caught.requestId }
            : { message: caught instanceof Error ? caught.message : "Request failed." }
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nonce, ...deps]);

  return { data, error, loading, reload };
}
