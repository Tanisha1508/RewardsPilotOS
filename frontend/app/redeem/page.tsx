"use client";

import { useState } from "react";
import { api, ApiRequestError } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import { Empty, ErrorNotice, Shell, WakingNotice } from "@/components/shell";
import { currencyLabel } from "@/lib/display";
import type { RewardBalance } from "@/types/api";

// Redeem — what your points can become (BUILD_SPEC §10).
//
// Replaces the old /transfer page, which was a search box over the knowledge
// corpus. The data was right and the framing was wrong: it asked the user to
// search our documents instead of answering "what can I do with what I have".
// Nobody could tell what the page was for, which is a design finding, not a
// docs problem.
//
// Now it is driven by the balances on the Portfolio page: one section per
// currency you actually hold. Same verified corpus, same sources and freshness
// dates — asked on the user's behalf rather than by them.
//
// Two sections only. Goals belong here (what you are aiming at); loyalty
// accounts moved to Portfolio (they are holdings). Reward preferences moved to
// Settings. Four sections made this unreadable.

const GOAL_TYPES = [
  { value: "trip", label: "Trip", hint: "somewhere you want to go" },
  { value: "redemption", label: "Redemption", hint: "a specific award you want to book" },
  { value: "savings", label: "Savings", hint: "a points balance you want to reach" },
] as const;

const EMPTY_GOAL = {
  goal_type: "redemption" as (typeof GOAL_TYPES)[number]["value"],
  description: "",
  target_date: "",
};

export default function RedeemPage() {
  const balances = useApi(() => api.listBalances());
  const goals = useApi(() => api.listGoals());

  const [goalForm, setGoalForm] = useState(EMPTY_GOAL);
  const [addingGoal, setAddingGoal] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<{ message: string; requestId?: string } | null>(null);

  async function addGoal(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api.createGoal({
        goal_type: goalForm.goal_type,
        description: goalForm.description.trim(),
        // Empty means no deadline, not today. The engine treats them differently.
        target_date: goalForm.target_date === "" ? null : goalForm.target_date,
        status: "active",
      });
      setGoalForm(EMPTY_GOAL);
      setAddingGoal(false);
      goals.reload();
    } catch (caught) {
      setError(
        caught instanceof ApiRequestError
          ? { message: caught.message, requestId: caught.requestId }
          : { message: caught instanceof Error ? caught.message : "Request failed." }
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <Shell>
      <h1 className="text-lg font-semibold tracking-tight">Redeem</h1>
      <p className="mt-1 max-w-2xl text-sm text-neutral-400">
        What your points can become — where they transfer, and how far they get you.
      </p>

      {error ? (
        <div className="mt-4">
          <ErrorNotice error={error} />
        </div>
      ) : null}

      {/* ---- where your points can go ---- */}
      <section className="mt-8">
        <h2 className="text-sm font-medium text-neutral-300">Where your points can go</h2>
        <p className="mt-1 max-w-2xl text-xs text-neutral-500">
          Verified transfer partners for the balances you hold, with each issuer&apos;s own caps and
          dates.
        </p>

        <div className="mt-4">
          {balances.error ? (
            <ErrorNotice error={balances.error} />
          ) : balances.loading ? (
            balances.slow ? (
              <WakingNotice context="Loading your balances" />
            ) : (
              <p className="text-sm text-neutral-500">Loading…</p>
            )
          ) : !balances.data?.length ? (
            // Not "no transfer options" — we simply do not know what you hold.
            // The two readings are opposite and only one is true.
            <Empty message="No balances recorded yet. Add a card and record its balance in Portfolio, then transfer options appear here." />
          ) : (
            <div className="space-y-4">
              {balances.data.map((balance) => (
                <CurrencyTransfers key={balance.balance_id} balance={balance} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ---- goals ---- */}
      <section className="mt-10">
        <div className="flex items-baseline justify-between gap-4">
          <div>
            <h2 className="text-sm font-medium text-neutral-300">Your goals</h2>
            <p className="mt-1 max-w-2xl text-xs text-neutral-500">
              What you are saving toward. Ask uses these to work out how far your balances get you.
            </p>
          </div>
          {!addingGoal ? (
            <button
              onClick={() => setAddingGoal(true)}
              className="shrink-0 rounded border border-neutral-800 px-2.5 py-1 text-xs text-neutral-300 hover:border-accent hover:text-accent"
            >
              + Add a goal
            </button>
          ) : null}
        </div>

        {/* Behind a disclosure, not permanently open: a form you fill in once
            should not occupy the page on every later visit. */}
        {addingGoal ? (
          <form
            onSubmit={addGoal}
            className="mt-4 rounded border border-neutral-800 bg-neutral-900/40 p-4"
          >
            <div className="grid gap-3 sm:grid-cols-4">
              <label className="block text-xs text-neutral-500">
                Type
                <select
                  value={goalForm.goal_type}
                  onChange={(e) =>
                    setGoalForm({
                      ...goalForm,
                      goal_type: e.target.value as typeof goalForm.goal_type,
                    })
                  }
                  className="mt-1 w-full rounded border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-accent"
                >
                  {GOAL_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-xs text-neutral-500 sm:col-span-2">
                What are you aiming for?
                <input
                  autoFocus
                  required
                  value={goalForm.description}
                  onChange={(e) => setGoalForm({ ...goalForm, description: e.target.value })}
                  placeholder="Business class to Singapore"
                  className="mt-1 w-full rounded border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-accent"
                />
              </label>
              <label className="block text-xs text-neutral-500">
                By when <span className="text-neutral-600">optional</span>
                <input
                  type="date"
                  value={goalForm.target_date}
                  onChange={(e) => setGoalForm({ ...goalForm, target_date: e.target.value })}
                  className="mt-1 w-full rounded border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-accent"
                />
              </label>
            </div>
            <p className="mt-2 text-xs text-neutral-600">
              {GOAL_TYPES.find((t) => t.value === goalForm.goal_type)?.hint}
            </p>
            <div className="mt-3 flex gap-2">
              <button
                type="submit"
                disabled={busy}
                className="rounded bg-accent px-3 py-2 text-sm font-medium disabled:opacity-50"
              >
                {busy ? "Adding…" : "Add goal"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setAddingGoal(false);
                  setGoalForm(EMPTY_GOAL);
                }}
                className="rounded border border-neutral-800 px-3 py-2 text-sm text-neutral-300"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : null}

        <div className="mt-4">
          {goals.error ? (
            <ErrorNotice error={goals.error} />
          ) : goals.loading ? (
            <p className="text-sm text-neutral-500">Loading…</p>
          ) : !goals.data?.length ? (
            <Empty message="No goals yet. Add one and Ask will factor it in." />
          ) : (
            <table className="w-full text-sm">
              <thead className="text-left text-xs uppercase tracking-wide text-neutral-500">
                <tr>
                  <th className="py-2">Goal</th>
                  <th className="py-2">Type</th>
                  <th className="py-2">Target date</th>
                  <th className="py-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-900">
                {goals.data.map((goal) => (
                  <tr key={goal.goal_id}>
                    <td className="py-2">{goal.description}</td>
                    <td className="py-2 text-neutral-400">{goal.goal_type}</td>
                    {/* No deadline reads as "—", never a guessed date. */}
                    <td className="py-2 text-neutral-400">{goal.target_date ?? "—"}</td>
                    <td className="py-2 text-neutral-400">{goal.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {goals.data?.length ? (
          <p className="mt-4 max-w-2xl text-xs text-neutral-600">
            Goals can be added but not yet edited or removed — the API has no update or delete route
            for them.
          </p>
        ) : null}
      </section>
    </Shell>
  );
}

/** Transfer options for one currency the user actually holds.
 *
 *  Each block runs its own retrieval, scoped to that currency's issuer and to
 *  `transfer_rules` documents. Per-currency rather than one combined search so a
 *  slow or empty result for one holding never hides the others — and so the
 *  answer is visibly *about* that balance. */
function CurrencyTransfers({ balance }: { balance: RewardBalance }) {
  const chunks = useApi(
    () =>
      api.searchKnowledge({
        q: `${currencyLabel(balance.reward_currency)} transfer partners ratios caps`,
        doc_type: "transfer_rules",
        k: 4,
      }),
    [balance.reward_currency]
  );

  return (
    <div className="rounded-lg border border-neutral-800 bg-neutral-900/40 px-5 py-4">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="text-base font-semibold tabular-nums">
          {balance.current_balance.toLocaleString("en-IN")}
        </span>
        <span className="text-sm text-neutral-300">{currencyLabel(balance.reward_currency)}</span>
        {balance.expiry_date ? (
          <span className="text-xs text-amber-200/80">expires {balance.expiry_date}</span>
        ) : null}
      </div>

      <div className="mt-3">
        {chunks.error ? (
          <ErrorNotice error={chunks.error} />
        ) : chunks.loading ? (
          chunks.slow ? (
            <p className="text-xs text-neutral-500">
              Building the knowledge index — this takes up to two minutes once after a restart, then
              seconds.
            </p>
          ) : (
            <p className="text-xs text-neutral-500">Looking up transfer partners…</p>
          )
        ) : !chunks.data?.chunks.length ? (
          // Missing data, never "there are no options" — opposite meanings.
          <p className="text-xs text-neutral-500">
            We hold no verified transfer data for {currencyLabel(balance.reward_currency)}.
          </p>
        ) : (
          <div className="space-y-3">
            {chunks.data.chunks.map((chunk) => (
              <div key={`${chunk.doc_id}-${chunk.chunk_index}`} className="text-sm">
                <p className="leading-relaxed text-neutral-300">{chunk.content}</p>
                <p className="mt-1 text-xs">
                  <a
                    href={`https://${chunk.metadata.source_url.replace(/^https?:\/\//, "")}`}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="text-accent-soft hover:underline"
                  >
                    {chunk.metadata.source_url.replace(/^https?:\/\//, "")}
                  </a>
                  {/* Freshness is part of the claim, not decoration. */}
                  <span className="ml-2 rounded bg-neutral-900 px-1.5 py-0.5 text-neutral-500">
                    {chunk.metadata.last_changed}
                  </span>
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
