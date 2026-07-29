"use client";

import { useState } from "react";
import { api, ApiRequestError } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import { Empty, ErrorNotice, Shell, WakingNotice } from "@/components/shell";

// Travel goals (BUILD_SPEC §10, MASTER_SPEC ch. 21).
//
// `GetTravelGoals` is a registered tool the Planner is told to use for portfolio
// questions, and it is Postgres-backed — but with no UI it returned an empty
// list forever, so redemption reasoning had no target to aim at. This page is
// what makes that tool mean anything.
//
// A goal is what you are saving toward ("business class to Singapore"), which is
// what turns "you have 15,000 EDGE Miles" into "you are 37,000 short".

const GOAL_TYPES = [
  { value: "trip", label: "Trip", hint: "somewhere you want to go" },
  { value: "redemption", label: "Redemption", hint: "a specific award you want to book" },
  { value: "savings", label: "Savings", hint: "a points balance you want to reach" },
] as const;

const EMPTY_FORM = {
  goal_type: "trip" as (typeof GOAL_TYPES)[number]["value"],
  description: "",
  target_date: "",
};

export default function GoalsPage() {
  const goals = useApi(() => api.listGoals());
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<{ message: string; requestId?: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function addGoal(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api.createGoal({
        goal_type: form.goal_type,
        description: form.description.trim(),
        // Empty date is null, not today — "no deadline" and "due now" are
        // different facts and the engine treats them differently.
        target_date: form.target_date === "" ? null : form.target_date,
        status: "active",
      });
      setForm(EMPTY_FORM);
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
      <h1 className="text-lg font-semibold tracking-tight">Goals</h1>
      <p className="mt-1 max-w-2xl text-sm text-neutral-400">
        What you are saving toward. Ask uses these to work out how far your balances get you, and
        what is still missing.
      </p>

      <form onSubmit={addGoal} className="mt-6 grid gap-3 sm:grid-cols-5">
        <label className="block text-xs text-neutral-500">
          Type
          <select
            value={form.goal_type}
            onChange={(e) =>
              setForm({ ...form, goal_type: e.target.value as typeof form.goal_type })
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
          Description
          <input
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Business class to Singapore"
            required
            className="mt-1 w-full rounded border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-accent"
          />
        </label>

        <label className="block text-xs text-neutral-500">
          Target date
          <input
            type="date"
            value={form.target_date}
            onChange={(e) => setForm({ ...form, target_date: e.target.value })}
            className="mt-1 w-full rounded border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-accent"
          />
        </label>

        <div className="flex items-end">
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded bg-accent px-3 py-2 text-sm font-medium disabled:opacity-50"
          >
            {busy ? "Adding…" : "Add goal"}
          </button>
        </div>
      </form>

      <p className="mt-2 text-xs text-neutral-600">
        {GOAL_TYPES.find((t) => t.value === form.goal_type)?.hint}
      </p>

      {error ? (
        <div className="mt-4">
          <ErrorNotice error={error} />
        </div>
      ) : null}

      <section className="mt-8">
        {goals.error ? (
          <ErrorNotice error={goals.error} />
        ) : goals.loading ? (
          goals.slow ? (
            <WakingNotice context="Loading goals" />
          ) : (
            <p className="text-sm text-neutral-500">Loading…</p>
          )
        ) : !goals.data?.length ? (
          <Empty message="No goals yet. Add one above and Ask will factor it in." />
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
                  {/* No deadline reads as "—", never as a guessed date. */}
                  <td className="py-2 text-neutral-400">{goal.target_date ?? "—"}</td>
                  <td className="py-2 text-neutral-400">{goal.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* Same honest gap as preferences: the API exposes GET and POST only.
          Editing or removing a goal needs new endpoints, which is an API
          contract change (CLAUDE.md build constraints) and waits for a spec
          decision rather than being invented here. */}
      {goals.data?.length ? (
        <p className="mt-8 max-w-2xl text-xs text-neutral-600">
          Goals can be added but not yet edited or removed — the API has no update or delete route
          for them.
        </p>
      ) : null}
    </Shell>
  );
}
