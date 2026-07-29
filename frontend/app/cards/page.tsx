"use client";

import { useState } from "react";
import { api, ApiRequestError } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import { Empty, ErrorNotice, Shell } from "@/components/shell";
import type { Card, CardPatch, RewardBalance } from "@/types/api";

// Cards CRUD (BUILD_SPEC §10). Annual fee is optional and stays empty rather
// than defaulting to 0 — an unknown fee and a waived fee are different facts,
// and the project's rule is that unknown beats incorrect.

/** Cards the Rule Engine can actually compute for.
 *
 *  Mirrors `rules/parser/catalog.py` (and the reward_currency each rule file
 *  declares). Hand-written to match, per the project's no-codegen convention for
 *  API types — kept to the same three cards the catalogue resolves, so drift is
 *  visible rather than subtle. When a card graduates from VERIFICATION_QUEUE,
 *  it gets a line there and a line here.
 *
 *  The point is not convenience. `reward_currency` must match a transfer-graph
 *  node id and (issuer, card_name) must match the catalogue, and both were free
 *  text: one typo produced a card that tracked fine and silently computed
 *  nothing. */
const KNOWN_CARDS = [
  {
    label: "HDFC Infinia",
    issuer: "hdfc",
    card_name: "HDFC Infinia",
    network: "visa",
    reward_currency: "hdfc_reward_points",
  },
  {
    label: "Axis Bank Atlas",
    issuer: "axis",
    card_name: "Axis Bank Atlas",
    network: "visa",
    reward_currency: "edge_miles",
  },
  {
    label: "Amex Platinum Travel",
    issuer: "amex",
    card_name: "Amex Platinum Travel",
    network: "amex",
    reward_currency: "membership_rewards",
  },
] as const;

const EMPTY_FORM = {
  issuer: "",
  card_name: "",
  network: "visa",
  reward_currency: "",
  annual_fee: "",
  renewal_date: "",
};

export default function CardsPage() {
  const cards = useApi(() => api.listCards());
  const balances = useApi(() => api.listBalances());
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<{ message: string; requestId?: string } | null>(null);
  const [busy, setBusy] = useState(false);

  const balanceOf = (card: Card) =>
    balances.data?.find((entry) => entry.card_id === card.card_id) ?? null;

  /** Record a points balance against a card.
   *
   *  Transfer and redemption questions cannot be answered without balances —
   *  "how do I get to KrisFlyer" needs to know what you hold. The endpoint and
   *  its typed client both existed; no page called them, so the dashboard said
   *  "record its balance" with nowhere to do it. */
  async function saveBalance(card: Card, raw: string) {
    const value = Number(raw);
    if (raw.trim() === "" || Number.isNaN(value) || value < 0) {
      setError({ message: "Balance must be a number of points, zero or more." });
      return;
    }
    setError(null);
    try {
      await api.setBalance(card.card_id, {
        // The card's own currency — never a typed one, which would create a
        // balance under a currency the transfer graph does not link to it.
        reward_currency: card.reward_currency,
        current_balance: value,
      });
      balances.reload();
    } catch (caught) {
      setError(toNotice(caught));
    }
  }

  async function addCard(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api.addCard({
        issuer: form.issuer.trim(),
        card_name: form.card_name.trim(),
        network: form.network.trim(),
        reward_currency: form.reward_currency.trim(),
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

  /** Edit a card in place.
   *
   *  Without this the only way to fix a typo was delete-and-re-add, which drops
   *  the card's recorded balance with it — a data-loss trap sitting behind a
   *  one-character mistake. */
  async function patchCard(card: Card, changes: CardPatch) {
    setError(null);
    try {
      await api.updateCard(card.card_id, changes);
      cards.reload();
    } catch (caught) {
      setError(toNotice(caught));
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
      <p className="mt-1 max-w-2xl text-sm text-neutral-400">
        The cards you hold, and how many points sit on each. Ask compares only these — add a card
        before asking which one to use.
      </p>

      {/* Pick a supported card and the four identity fields fill themselves.
          Typing them by hand still works — the catalogue is deliberately small,
          and refusing unknown cards would be worse than tracking them. */}
      <div className="mt-6 flex flex-wrap items-center gap-2 text-sm">
        <span className="text-xs text-neutral-500">Quick add:</span>
        {KNOWN_CARDS.map((card) => (
          <button
            key={card.label}
            type="button"
            onClick={() =>
              setForm({
                ...EMPTY_FORM,
                issuer: card.issuer,
                card_name: card.card_name,
                network: card.network,
                reward_currency: card.reward_currency,
              })
            }
            className="rounded border border-neutral-800 px-2.5 py-1 text-xs text-neutral-300 hover:border-accent hover:text-accent"
          >
            {card.label}
          </button>
        ))}
      </div>

      <form onSubmit={addCard} className="mt-3 grid gap-3 sm:grid-cols-7">
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
          label="Reward currency"
          value={form.reward_currency}
          onChange={(v) => setForm({ ...form, reward_currency: v })}
          placeholder="hdfc_reward_points"
          required
        />
        <Field
          label="Annual fee"
          value={form.annual_fee}
          onChange={(v) => setForm({ ...form, annual_fee: v })}
          placeholder="optional"
          type="number"
        />
        {/* Drives annual-fee and milestone reasoning. The form collected it in
            state from the start but never rendered an input, so every card
            added through the UI had a null renewal date and the "Renews" column
            was permanently "—". */}
        <Field
          label="Renews on"
          value={form.renewal_date}
          onChange={(v) => setForm({ ...form, renewal_date: v })}
          placeholder="optional"
          type="date"
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
                <th className="py-2 text-right">Balance</th>
                <th className="py-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-900">
              {cards.data.map((card) => (
                <tr key={card.card_id}>
                  <td className="py-2">
                    {card.card_name}
                    {/* Tracked but not computable. Silence here is what makes a
                        typo look like a working card until you ask a question
                        about it and get nothing back. */}
                    {card.card_key === null ? (
                      <span
                        className="ml-2 rounded border border-amber-800 bg-amber-950/40 px-1.5 py-0.5 text-[10px] text-amber-200"
                        title="No verified rule file matches this issuer and card name, so Ask cannot compute rewards for it. Check the spelling, or use Quick add."
                      >
                        not recognised
                      </span>
                    ) : null}
                  </td>
                  <td className="py-2 text-neutral-400">{card.issuer}</td>
                  <td className="py-2 text-neutral-400">{card.network}</td>
                  <td className="py-2 text-right tabular-nums">
                    {/* Unknown, not zero. */}
                    <EditableCell
                      display={
                        card.annual_fee === null
                          ? "unknown"
                          : `₹${card.annual_fee.toLocaleString("en-IN")}`
                      }
                      value={card.annual_fee === null ? "" : String(card.annual_fee)}
                      type="number"
                      onSave={(v) =>
                        patchCard(card, { annual_fee: v.trim() === "" ? null : Number(v) })
                      }
                    />
                  </td>
                  <td className="py-2 text-right text-neutral-400">
                    <EditableCell
                      display={card.renewal_date ?? "—"}
                      value={card.renewal_date ?? ""}
                      type="date"
                      onSave={(v) => patchCard(card, { renewal_date: v === "" ? null : v })}
                    />
                  </td>
                  <td className="py-2 text-right">
                    <BalanceCell
                      card={card}
                      balance={balanceOf(card)}
                      onSave={(value) => saveBalance(card, value)}
                    />
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

/** Click-to-edit table cell. Shows the rendered value until clicked, then an
 *  input; Enter saves, Escape abandons. Kept generic so annual fee and renewal
 *  date share one behaviour rather than growing two near-identical widgets. */
function EditableCell({
  display,
  value,
  type,
  onSave,
}: {
  display: string;
  value: string;
  type: "number" | "date" | "text";
  onSave: (value: string) => void | Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);

  if (!editing) {
    return (
      <button
        onClick={() => {
          setDraft(value);
          setEditing(true);
        }}
        className="hover:text-accent"
        title="Click to edit"
      >
        {display}
      </button>
    );
  }

  const commit = () => {
    void onSave(draft);
    setEditing(false);
  };

  return (
    <input
      autoFocus
      type={type}
      value={draft}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={commit}
      onKeyDown={(e) => {
        if (e.key === "Enter") commit();
        if (e.key === "Escape") setEditing(false);
      }}
      className="w-32 rounded border border-neutral-800 bg-neutral-900 px-2 py-1 text-right text-sm outline-none focus:border-accent"
    />
  );
}

/** Inline balance editor.
 *
 *  `last_updated` is shown rather than hidden: balances are user-entered and go
 *  stale, and how old the number is forms part of the answer
 *  (KNOWN_LIMITATIONS 1). An unrecorded balance reads "not recorded", never 0 —
 *  holding no points and not having told us are different facts. */
function BalanceCell({
  card,
  balance,
  onSave,
}: {
  card: Card;
  balance: RewardBalance | null;
  onSave: (value: string) => void | Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");

  if (!editing) {
    return (
      <button
        onClick={() => {
          setDraft(balance ? String(balance.current_balance) : "");
          setEditing(true);
        }}
        className="text-right hover:text-accent"
        title={
          balance
            ? `${card.reward_currency} · updated ${balance.last_updated}`
            : `Record a ${card.reward_currency} balance`
        }
      >
        {balance ? (
          <span className="tabular-nums">
            {balance.current_balance.toLocaleString("en-IN")}
          </span>
        ) : (
          <span className="text-xs text-neutral-500">not recorded</span>
        )}
      </button>
    );
  }

  return (
    <span className="inline-flex items-center gap-1">
      <input
        autoFocus
        type="number"
        min={0}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            void onSave(draft);
            setEditing(false);
          }
          if (e.key === "Escape") setEditing(false);
        }}
        className="w-24 rounded border border-neutral-800 bg-neutral-900 px-2 py-1 text-right text-sm tabular-nums outline-none focus:border-accent"
      />
      <button
        onClick={() => {
          void onSave(draft);
          setEditing(false);
        }}
        className="text-xs text-accent"
      >
        Save
      </button>
    </span>
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
