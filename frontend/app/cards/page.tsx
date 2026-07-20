"use client";

import { useState } from "react";
import { api, ApiRequestError } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import { Empty, ErrorNotice, Shell } from "@/components/shell";
import type { Card } from "@/types/api";

// Cards CRUD (BUILD_SPEC §10). Annual fee is optional and stays empty rather
// than defaulting to 0 — an unknown fee and a waived fee are different facts,
// and the project's rule is that unknown beats incorrect.

const EMPTY_FORM = {
  issuer: "",
  card_name: "",
  network: "visa",
  annual_fee: "",
  renewal_date: "",
};

export default function CardsPage() {
  const cards = useApi(() => api.listCards());
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<{ message: string; requestId?: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function addCard(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api.addCard({
        issuer: form.issuer.trim(),
        card_name: form.card_name.trim(),
        network: form.network.trim(),
        annual_fee: form.annual_fee === "" ? null : Number(form.annual_fee),
        renewal_date: form.renewal_date === "" ? null : form.renewal_date,
        joining_date: null,
        status: "active",
      });
      setForm(EMPTY_FORM);
      cards.reload();
    } catch (caught) {
      setError(toNotice(caught));
    } finally {
      setBusy(false);
    }
  }

  async function removeCard(card: Card) {
    setError(null);
    try {
      await api.deleteCard(card.card_id);
      cards.reload();
    } catch (caught) {
      setError(toNotice(caught));
    }
  }

  return (
    <Shell>
      <h1 className="text-lg font-semibold tracking-tight">Cards</h1>

      <form onSubmit={addCard} className="mt-6 grid gap-3 sm:grid-cols-5">
        <Field
          label="Issuer"
          value={form.issuer}
          onChange={(v) => setForm({ ...form, issuer: v })}
          placeholder="hdfc"
          required
        />
        <Field
          label="Card name"
          value={form.card_name}
          onChange={(v) => setForm({ ...form, card_name: v })}
          placeholder="HDFC Infinia"
          required
        />
        <Field
          label="Network"
          value={form.network}
          onChange={(v) => setForm({ ...form, network: v })}
          placeholder="visa"
          required
        />
        <Field
          label="Annual fee"
          value={form.annual_fee}
          onChange={(v) => setForm({ ...form, annual_fee: v })}
          placeholder="optional"
          type="number"
        />
        <div className="flex items-end">
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded bg-accent px-3 py-2 text-sm font-medium disabled:opacity-50"
          >
            {busy ? "Adding…" : "Add card"}
          </button>
        </div>
      </form>

      {error ? (
        <div className="mt-4">
          <ErrorNotice error={error} />
        </div>
      ) : null}

      <section className="mt-8">
        {cards.error ? (
          <ErrorNotice error={cards.error} />
        ) : cards.loading ? (
          <p className="text-sm text-neutral-500">Loading…</p>
        ) : !cards.data?.length ? (
          <Empty message="No cards yet. Add one above." />
        ) : (
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase tracking-wide text-neutral-500">
              <tr>
                <th className="py-2">Card</th>
                <th className="py-2">Issuer</th>
                <th className="py-2">Network</th>
                <th className="py-2 text-right">Annual fee</th>
                <th className="py-2 text-right">Renews</th>
                <th className="py-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-900">
              {cards.data.map((card) => (
                <tr key={card.card_id}>
                  <td className="py-2">{card.card_name}</td>
                  <td className="py-2 text-neutral-400">{card.issuer}</td>
                  <td className="py-2 text-neutral-400">{card.network}</td>
                  <td className="py-2 text-right tabular-nums">
                    {/* Unknown, not zero. */}
                    {card.annual_fee === null
                      ? "unknown"
                      : `₹${card.annual_fee.toLocaleString("en-IN")}`}
                  </td>
                  <td className="py-2 text-right text-neutral-400">
                    {card.renewal_date ?? "—"}
                  </td>
                  <td className="py-2 text-right">
                    <button
                      onClick={() => removeCard(card)}
                      className="text-xs text-neutral-500 hover:text-red-300"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </Shell>
  );
}

function toNotice(caught: unknown) {
  return caught instanceof ApiRequestError
    ? { message: caught.message, requestId: caught.requestId }
    : { message: caught instanceof Error ? caught.message : "Request failed." };
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  required,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
  type?: string;
}) {
  return (
    <label className="block text-xs text-neutral-500">
      {label}
      <input
        type={type}
        value={value}
        required={required}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full rounded border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-accent"
      />
    </label>
  );
}
