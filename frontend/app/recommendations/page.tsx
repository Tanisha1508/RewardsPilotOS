"use client";

import { useState } from "react";
import Link from "next/link";
import { api, ApiRequestError } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import { Empty, ErrorNotice, Shell, WakingNotice } from "@/components/shell";
import { RecommendationCard } from "@/components/recommendation-card";
import type { FeedbackStatus } from "@/types/api";

// Recommendation history (BUILD_SPEC §10).
//
// `api.listRecommendations()` and the persistence behind it both existed from
// D4; no page called them, so the dashboard showed a bare count and the Ask
// page showed only the answer you had just asked for. That made stored
// recommendations, their feedback state, and the interaction events RecallMemory
// reads back on later queries all invisible — you could not check whether any of
// it worked.
//
// Renders through the same RecommendationCard as Ask, deliberately: a stored
// recommendation must show the same numbers, citations and confidence it showed
// when it was generated. A second renderer would be a second chance to drift.

const STATUS_STYLE: Record<string, string> = {
  accepted: "text-emerald-300",
  rejected: "text-red-300",
  saved: "text-sky-300",
  viewed: "text-neutral-500",
  generated: "text-neutral-500",
};

export default function RecommendationsPage() {
  const recommendations = useApi(() => api.listRecommendations());
  const [error, setError] = useState<{ message: string; requestId?: string } | null>(null);

  async function sendFeedback(recId: string, status: FeedbackStatus) {
    setError(null);
    try {
      await api.sendFeedback(recId, status);
      // Reload rather than patching locally: the stored status is the truth,
      // and showing an optimistic value that never persisted is the failure
      // this page exists to make visible.
      recommendations.reload();
    } catch (caught) {
      setError(
        caught instanceof ApiRequestError
          ? { message: caught.message, requestId: caught.requestId }
          : { message: caught instanceof Error ? caught.message : "Request failed." }
      );
    }
  }

  return (
    <Shell>
      <h1 className="text-lg font-semibold tracking-tight">History</h1>
      <p className="mt-1 text-sm text-neutral-400">
        Every recommendation you have asked for, with the numbers and sources it was given at the
        time.
      </p>
      {/* Retention, stated (privacy audit P4). "Kept indefinitely" was the
          honest answer until DELETE /auth/me existed and there was nothing a
          user could do about it. Now the honest answer is "until you delete
          it", which is only worth saying because the second half is true. */}
      <p className="mt-1 max-w-2xl text-xs text-neutral-600">
        These are kept until you delete them. Removing your data in{" "}
        <Link href="/account" className="text-accent-soft hover:underline">
          Account
        </Link>{" "}
        erases this history along with everything else.
      </p>

      {error ? (
        <div className="mt-4">
          <ErrorNotice error={error} />
        </div>
      ) : null}

      <section className="mt-6 space-y-6">
        {recommendations.error ? (
          <ErrorNotice error={recommendations.error} />
        ) : recommendations.loading ? (
          recommendations.slow ? (
            <WakingNotice context="Loading your history" />
          ) : (
            <p className="text-sm text-neutral-500">Loading…</p>
          )
        ) : !recommendations.data?.length ? (
          <Empty message="No recommendations yet. Ask a question and it will appear here." />
        ) : (
          recommendations.data.map((rec) => (
            <article key={rec.rec_id}>
              <header className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
                <p className="text-sm text-neutral-300">
                  <span className="text-neutral-500">You asked:</span> {rec.query}
                </p>
                <p className="text-xs text-neutral-600">
                  <time dateTime={rec.created_at}>{formatWhen(rec.created_at)}</time>
                  <span className={`ml-2 ${STATUS_STYLE[rec.status] ?? "text-neutral-500"}`}>
                    {rec.status}
                  </span>
                </p>
              </header>
              <RecommendationCard
                rec={rec}
                onFeedback={(status) => sendFeedback(rec.rec_id, status)}
              />
            </article>
          ))
        )}
      </section>
    </Shell>
  );
}

/** Absolute, not "3 hours ago". Freshness is load-bearing in this product, and
 *  a relative label hides how stale a stored answer's sources are. */
function formatWhen(iso: string) {
  const parsed = new Date(iso);
  return Number.isNaN(parsed.valueOf())
    ? iso
    : parsed.toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
}
