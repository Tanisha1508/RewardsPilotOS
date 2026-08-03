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
  error?: { message: string; requestId?: string; code?: string };
  /** The connection died but the server is still writing. See `recover`. */
  recovering?: boolean;
}

// A question takes around 29 seconds warm, and the same-origin rewrite ends any
// request at 30. The first question after a restart, which also pays for the
// knowledge index, ran to 100 s on 2026-08-03 and was cut off — while the
// backend finished the work and saved the answer. The user was shown an error
// for an answer that existed.
//
// So a cut-off request is not a failed question, and the honest response is not
// to ask again: asking again would spend a second question against the daily
// limit and a second pair of model calls, to produce an answer already sitting
// in the database. We collect the one that finished instead.
//
// Identified by id rather than by timestamp. Client and server clocks disagree
// by unknown amounts, and "newer than when I asked" is exactly the kind of
// almost-right rule that would occasionally show somebody the wrong answer;
// "an id that did not exist when I asked" cannot.
const RECOVER_ATTEMPTS = 12;
const RECOVER_EVERY_MS = 5000;

async function recover(query: string, before: Set<string>): Promise<Recommendation | null> {
  for (let attempt = 0; attempt < RECOVER_ATTEMPTS; attempt++) {
    await new Promise((resolve) => setTimeout(resolve, RECOVER_EVERY_MS));
    const saved = await api.listRecommendations().catch(() => null);
    const match = saved?.find((rec) => !before.has(rec.rec_id) && rec.query === query);
    if (match) return match;
  }
  return null;
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

    // Taken before the question, not after: once the answer is saved it is
    // indistinguishable from an identical question asked earlier. A failure
    // here costs nothing — an empty set just means every answer looks new, and
    // the query still has to match.
    const before = new Set(
      ((await api.listRecommendations().catch(() => [])) ?? []).map((rec) => rec.rec_id)
    );

    const update = (patch: Partial<Turn>) =>
      setTurns((t) => t.map((turn, i) => (i === index ? { ...turn, ...patch } : turn)));

    try {
      const rec = await api.chat(q);
      update({ rec });
    } catch (caught) {
      const error =
        caught instanceof ApiRequestError
          ? { message: caught.message, requestId: caught.requestId, code: caught.code }
          : { message: caught instanceof Error ? caught.message : "Request failed." };

      if (error.code === "malformed_response") {
        update({ recovering: true });
        const rescued = await recover(q, before);
        if (rescued) {
          update({ rec: rescued, recovering: false });
          return;
        }
        // Nothing arrived. The original message is right after all — the work
        // may still be running, and History is where it will appear.
        update({ recovering: false, error });
        return;
      }

      update({ error });
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
              ) : turn.recovering ? (
                // Not a retry, and worth not implying one: the question was
                // asked once and is still being answered on the server.
                <p className="text-sm text-neutral-500">
                  Still working. This one is taking longer than the connection stays open, so we are
                  waiting for the answer to land rather than asking again.
                </p>
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
