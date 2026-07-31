"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, ApiRequestError } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import { ErrorNotice, Shell, WakingNotice } from "@/components/shell";
import { RecommendationCard } from "@/components/recommendation-card";
import type { FeedbackStatus } from "@/types/api";

// One stored answer, on its own page (A9).
//
// `GET /api/v1/recommendations/{id}` and `api.getRecommendation` both existed
// from D4; only this page was missing, so there was no way to link to a single
// answer — the whole of History was the smallest thing you could point someone
// at. The 2026-07-31 wiring sweep confirmed the two halves were already there
// (`docs/WIRING_SWEEP.md`).
//
// Renders through the same `RecommendationCard` as Ask and History, which is
// the point: a linked answer must show the numbers, citations and confidence it
// was given at the time, not a second rendering that can drift from them.
//
// Ownership is the server's job. The route reports another user's answer as
// 404, never 403 — telling someone "that exists, just not yours" confirms the
// existence of another user's data. So this page needs no ownership logic; it
// only has to render the 404 honestly.

export default function RecommendationPage() {
  const params = useParams<{ rec_id: string }>();
  const recId = params?.rec_id ?? "";

  const recommendation = useApi(() => api.getRecommendation(recId), [recId]);
  const cards = useApi(() => api.listCards());
  const cardNames = Object.fromEntries(
    (cards.data ?? []).filter((c) => c.card_key).map((c) => [c.card_key as string, c.card_name])
  );

  const [error, setError] = useState<{ message: string; requestId?: string } | null>(null);

  async function sendFeedback(status: FeedbackStatus) {
    setError(null);
    try {
      await api.sendFeedback(recId, status);
      recommendation.reload();
    } catch (caught) {
      setError(
        caught instanceof ApiRequestError
          ? { message: caught.message, requestId: caught.requestId }
          : { message: caught instanceof Error ? caught.message : "Request failed." }
      );
    }
  }

  const rec = recommendation.data;

  return (
    <Shell>
      <Link href="/recommendations" className="text-sm text-accent-soft hover:underline">
        ← All questions
      </Link>

      {recommendation.error ? (
        <div className="mt-4">
          {/* A missing id and someone else's id look identical here, by design.
              Saying "not found" for both is the honest thing this page can say. */}
          <ErrorNotice error={recommendation.error} />
        </div>
      ) : recommendation.loading ? (
        <div className="mt-6">
          {recommendation.slow ? (
            <WakingNotice context="Loading this answer" />
          ) : (
            <p className="text-sm text-neutral-500">Loading…</p>
          )}
        </div>
      ) : rec ? (
        <article className="mt-4">
          <header className="mb-3">
            <p className="text-sm text-neutral-300">
              <span className="text-neutral-500">You asked:</span> {rec.query}
            </p>
            <p className="mt-1 text-xs text-neutral-600">
              <time dateTime={rec.created_at}>{formatWhen(rec.created_at)}</time>
              <span className="ml-2">{rec.status}</span>
            </p>
          </header>

          {error ? (
            <div className="mb-3">
              <ErrorNotice error={error} />
            </div>
          ) : null}

          <RecommendationCard rec={rec} cardNames={cardNames} onFeedback={sendFeedback} />

          <p className="mt-3 text-xs text-neutral-600">
            The numbers and sources above are the ones this answer was given when it was written.
            They are not recalculated on opening, so a rate that has changed since will not silently
            update here.
          </p>
        </article>
      ) : null}
    </Shell>
  );
}

/** Absolute, not "3 hours ago" — freshness is load-bearing in this product, and
 *  a relative label hides how stale a stored answer's sources are. Matches the
 *  History list deliberately. */
function formatWhen(iso: string) {
  const parsed = new Date(iso);
  return Number.isNaN(parsed.valueOf())
    ? iso
    : parsed.toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
}
