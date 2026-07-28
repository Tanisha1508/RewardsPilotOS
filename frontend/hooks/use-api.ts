"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiRequestError } from "@/lib/api";

export interface LoadState<T> {
  data: T | null;
  error: { message: string; requestId?: string } | null;
  loading: boolean;
  /** Still loading after SLOW_AFTER_MS. Almost always the Render free tier
   *  waking up (measured 15.6 s cold vs ~1.2 s warm, 2026-07-29), so the UI can
   *  say what is happening instead of showing a bare spinner that reads as
   *  broken. Distinct from `loading`: every request is loading, few are slow. */
  slow: boolean;
  reload: () => void;
}

/** Long enough that a normal warm request (~1.2 s) never trips it, short enough
 *  that a cold start is explained well before the user assumes it has hung. */
export const SLOW_AFTER_MS = 3000;

/** Load data from the API, keeping "loading", "failed", and "loaded but empty"
 *  distinct. Collapsing them is how a UI ends up showing "No cards" when what
 *  actually happened was a 500. */
export function useApi<T>(fetcher: () => Promise<T>, deps: unknown[] = []): LoadState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<LoadState<T>["error"]>(null);
  const [loading, setLoading] = useState(true);
  const [slow, setSlow] = useState(false);
  const [nonce, setNonce] = useState(0);

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setSlow(false);
    setError(null);

    const slowTimer = setTimeout(() => {
      if (!cancelled) setSlow(true);
    }, SLOW_AFTER_MS);

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
        clearTimeout(slowTimer);
        if (!cancelled) {
          setLoading(false);
          setSlow(false);
        }
      });

    return () => {
      cancelled = true;
      clearTimeout(slowTimer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nonce, ...deps]);

  return { data, error, loading, slow, reload };
}
