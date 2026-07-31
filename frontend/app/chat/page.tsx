"use client";

import { useState } from "react";
import Link from "next/link";
import { api, ApiRequestError } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import { DataNotice, ErrorNotice, Shell } from "@/components/shell";
import { RecommendationCard } from "@/components/recommendation-card";
import { formatDateTime } from "@/lib/display";
import type { FeedbackStatus, Recommendation } from "@/types/api";

// Chat (BUILD_SPEC §10): ask a question, get a recommendation card. One turn at
// a time — each query persists a recommendation the user can accept/reject/save.

interface Turn {
  query: string;
  rec?: Recommendation;
  error?: { message: string; requestId?: string };
}

export default function ChatPage() {
// card_key -> the card name the user gave it, so the numbers block reads
// "Axis Bank Atlas" rather than "axis_atlas" (A4). Deliberately tolerant: a
// stored answer can reference a card since deleted, and the calculation must
// still render, so the component falls back to a title-cased key.
  const cards = useApi(() => api.listCards());
  const cardNames = Object.fromEntries(
    (cards.data ?? []).filter((c) => c.card_key).map((c) => [c.card_key as string, c.card_name])
  );
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
        Which card to use, what your points are worth, how to get where you are going.
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

      <DataNotice />

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
                  cardNames={cardNames}
                  onFeedback={(status) => feedback(index, turn.rec!, status)}
                />
              ) : (
                <p className="text-sm text-neutral-500">Working through your cards…</p>
              )}
            </div>
          );
        })}
        {turns.length === 0 ? <Suggestions onPick={(q) => setQuery(q)} /> : null}
      </div>

      {/* Earlier questions, inline. Ask is home now, and a landing page that
          forgets every previous conversation reads as a tool rather than
          something that knows you. Only the three most recent — the full record
          is History, and duplicating it here would just be a second History. */}
      <RecentQuestions />
    </Shell>
  );
}

/** Openers for an empty Ask page.
 *
 *  Prefilling the box rather than submitting: a suggestion should show what a
 *  good question looks like, not spend one of a limited number of daily LLM
 *  calls on a question nobody actually asked. */
function Suggestions({ onPick }: { onPick: (q: string) => void }) {
  const EXAMPLES = [
    "Which of my cards is best for a ₹50,000 flight?",
    "What can I book with the points I have?",
    "How many points would a ₹20,000 hotel booking earn?",
  ];
  return (
    <div>
      <p className="text-sm text-neutral-500">Not sure where to start?</p>
      <div className="mt-3 grid gap-2">
        {EXAMPLES.map((q) => (
          <button
            key={q}
            onClick={() => onPick(q)}
            className="rounded border border-neutral-800 bg-neutral-900/40 px-3.5 py-2.5 text-left text-sm text-neutral-300 hover:border-accent hover:text-neutral-100"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

function RecentQuestions() {
  const recent = useApi(() => api.listRecommendations());
  const items = recent.data?.slice(0, 3) ?? [];

  // Silent when empty or broken: this is a convenience strip, and an error here
  // must not compete with the answer the page exists to show.
  if (recent.loading || recent.error || !items.length) return null;

  return (
    <section className="mt-12 border-t border-neutral-900 pt-6">
      <h2 className="text-xs uppercase tracking-wide text-neutral-500">Earlier questions</h2>
      <ul className="mt-3 divide-y divide-neutral-900">
        {items.map((rec) => (
          <li key={rec.rec_id} className="flex items-baseline justify-between gap-4 py-2.5">
            <Link
              href="/recommendations"
              className="text-sm text-neutral-300 hover:text-accent-soft"
            >
              {rec.query}
            </Link>
            <span className="shrink-0 text-xs text-neutral-600">
              {formatDateTime(rec.created_at)}
            </span>
          </li>
        ))}
      </ul>
      <Link
        href="/recommendations"
        className="mt-3 inline-block text-xs text-accent-soft hover:underline"
      >
        See all questions →
      </Link>
    </section>
  );
}
