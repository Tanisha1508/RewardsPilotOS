"use client";

import { useState } from "react";
import { api, ApiRequestError } from "@/lib/api";
import { ErrorNotice, Shell } from "@/components/shell";
import { RecommendationCard } from "@/components/recommendation-card";
import type { FeedbackStatus, Recommendation } from "@/types/api";

// Chat (BUILD_SPEC §10): ask a question, get a recommendation card. One turn at
// a time — each query persists a recommendation the user can accept/reject/save.

interface Turn {
  query: string;
  rec?: Recommendation;
  error?: { message: string; requestId?: string };
}

export default function ChatPage() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);

  async function ask(event: React.FormEvent) {
    event.preventDefault();
    const q = query.trim();
    if (!q) return;
    setQuery("");
    setBusy(true);
    const index = turns.length;
    setTurns((t) => [...t, { query: q }]);
    try {
      const rec = await api.chat(q);
      setTurns((t) => t.map((turn, i) => (i === index ? { ...turn, rec } : turn)));
    } catch (caught) {
      const error =
        caught instanceof ApiRequestError
          ? { message: caught.message, requestId: caught.requestId }
          : { message: caught instanceof Error ? caught.message : "Request failed." };
      setTurns((t) => t.map((turn, i) => (i === index ? { ...turn, error } : turn)));
    } finally {
      setBusy(false);
    }
  }

  async function feedback(index: number, rec: Recommendation, status: FeedbackStatus) {
    try {
      const updated = await api.sendFeedback(rec.rec_id, status);
      setTurns((t) => t.map((turn, i) => (i === index ? { ...turn, rec: updated } : turn)));
    } catch {
      // Non-fatal: leave the card as-is if feedback fails.
    }
  }

  return (
    <Shell>
      <h1 className="text-lg font-semibold tracking-tight">Ask</h1>
      <p className="mt-1 text-sm text-neutral-400">
        Ask about your cards — best card for a purchase, transfers, redemptions.
      </p>

      <form onSubmit={ask} className="mt-4 flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Which of my cards earns the most on flights?"
          className="flex-1 rounded border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-accent"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded bg-accent px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {busy ? "Thinking…" : "Ask"}
        </button>
      </form>

      <div className="mt-8 space-y-8">
        {[...turns].reverse().map((turn, revIndex) => {
          const index = turns.length - 1 - revIndex;
          return (
            <div key={index} className="space-y-3">
              <p className="text-sm text-neutral-400">
                <span className="text-neutral-600">You asked:</span> {turn.query}
              </p>
              {turn.error ? (
                <ErrorNotice error={turn.error} />
              ) : turn.rec ? (
                <RecommendationCard
                  rec={turn.rec}
                  onFeedback={(status) => feedback(index, turn.rec!, status)}
                />
              ) : (
                <p className="text-sm text-neutral-500">Working through your cards…</p>
              )}
            </div>
          );
        })}
        {turns.length === 0 ? (
          <p className="text-sm text-neutral-600">
            No questions yet. Try &ldquo;Which card is best for hotel bookings?&rdquo;
          </p>
        ) : null}
      </div>
    </Shell>
  );
}
