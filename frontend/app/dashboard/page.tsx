"use client";

import { api } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import { Empty, ErrorNotice, Shell } from "@/components/shell";

// Dashboard shell (BUILD_SPEC §10). D2 wires cards and balances; opportunities
// and expiring-points counts arrive with D5's opportunity engine, and are
// labelled as not-yet-wired rather than shown as zero — a confident "0
// opportunities" from a subsystem that does not exist yet is a lie.

export default function DashboardPage() {
  const portfolio = useApi(() => api.getPortfolio());
  const balances = useApi(() => api.listBalances());

  return (
    <Shell>
      <h1 className="text-lg font-semibold tracking-tight">Dashboard</h1>

      {portfolio.error ? <div className="mt-4"><ErrorNotice error={portfolio.error} /></div> : null}

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <Stat
          label="Cards"
          value={portfolio.loading ? "…" : String(portfolio.data?.cards.length ?? 0)}
        />
        <Stat
          label="Tracked balances"
          value={balances.loading ? "…" : String(balances.data?.length ?? 0)}
        />
        <Stat label="Opportunities" value="—" note="Wired in D5" />
      </div>

      <section className="mt-8">
        <h2 className="text-sm font-medium text-neutral-300">Reward balances</h2>
        {balances.error ? (
          <div className="mt-3">
            <ErrorNotice error={balances.error} />
          </div>
        ) : balances.loading ? (
          <p className="mt-3 text-sm text-neutral-500">Loading…</p>
        ) : !balances.data?.length ? (
          <div className="mt-3">
            <Empty message="No balances recorded yet. Add a card, then record its balance." />
          </div>
        ) : (
          <table className="mt-3 w-full text-sm">
            <thead className="text-left text-xs uppercase tracking-wide text-neutral-500">
              <tr>
                <th className="py-2">Currency</th>
                <th className="py-2 text-right">Balance</th>
                <th className="py-2 text-right">Expires</th>
                <th className="py-2 text-right">Last updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-900">
              {balances.data.map((balance) => (
                <tr key={balance.balance_id}>
                  <td className="py-2">{balance.reward_currency}</td>
                  <td className="py-2 text-right tabular-nums">
                    {balance.current_balance.toLocaleString("en-IN")}
                  </td>
                  <td className="py-2 text-right text-neutral-400">
                    {balance.expiry_date ?? "—"}
                  </td>
                  {/* Balances are user-entered; staleness is part of the answer. */}
                  <td className="py-2 text-right text-neutral-400">{balance.last_updated}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </Shell>
  );
}

function Stat({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="rounded border border-neutral-800 bg-neutral-900/40 px-4 py-3">
      <p className="text-xs uppercase tracking-wide text-neutral-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
      {note ? <p className="mt-1 text-xs text-neutral-600">{note}</p> : null}
    </div>
  );
}
