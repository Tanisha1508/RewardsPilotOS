"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiRequestError } from "@/lib/api";
import { KNOWN_CARDS } from "@/lib/known-cards";
import { ErrorNotice } from "@/components/shell";

// Guided setup for a new account.
//
// Every entry point used to land on a dashboard reading 0 / 0 / 0 — accurate and
// useless, since it never said what the product does or what to do next.
//
// A flow rather than one screen, because setup has a real dependency order:
// you cannot ask "how many EDGE Miles?" before knowing the person holds Atlas.
// Asking everything at once is what made the first attempt read as a form dump.
//
// Deliberately NOT wrapped in Shell: the nav is hidden here, because this is the
// one moment where wandering off leaves the product unable to answer anything.
// "Skip" is on every step, so it is a suggestion rather than a gate.

const STEPS = 4;

export default function WelcomePage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [picked, setPicked] = useState<string[]>([]);
  const [balances, setBalances] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<{ message: string; requestId?: string } | null>(null);
  const [created, setCreated] = useState<{ label: string; cardId: string; currency: string }[]>([]);

  const fail = (caught: unknown) =>
    setError(
      caught instanceof ApiRequestError
        ? { message: caught.message, requestId: caught.requestId }
        : { message: caught instanceof Error ? caught.message : "Request failed." }
    );

  /** Create the chosen cards, then advance. Done on leaving step 1 rather than
   *  at the end, so a failure surfaces next to the choice that caused it. */
  async function saveCards() {
    if (!picked.length) {
      setStep(4);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const made = [];
      for (const label of picked) {
        const card = KNOWN_CARDS.find((c) => c.label === label);
        if (!card) continue;
        const saved = await api.addCard({
          issuer: card.issuer,
          card_name: card.card_name,
          network: card.network,
          reward_currency: card.reward_currency,
          annual_fee: null,
          renewal_date: null,
          joining_date: null,
          status: "active",
        });
        made.push({ label, cardId: saved.card_id, currency: card.reward_currency });
      }
      setCreated(made);
      setStep(2);
    } catch (caught) {
      fail(caught);
    } finally {
      setBusy(false);
    }
  }

  /** Record whichever balances were filled in. Blank means "not recorded", never
   *  zero — holding no points and not having said are different facts. */
  async function saveBalances() {
    setBusy(true);
    setError(null);
    try {
      for (const card of created) {
        const raw = (balances[card.label] ?? "").replace(/,/g, "").trim();
        if (raw === "") continue;
        const value = Number(raw);
        if (Number.isNaN(value) || value < 0) continue;
        await api.setBalance(card.cardId, {
          reward_currency: card.currency,
          current_balance: value,
        });
      }
      setStep(3);
    } catch (caught) {
      fail(caught);
    } finally {
      setBusy(false);
    }
  }

  function next() {
    if (step === 1) return void saveCards();
    if (step === 2) return void saveBalances();
    if (step === 3) return setStep(4);
    router.push("/chat");
  }

  return (
    <div className="flex min-h-screen flex-col items-center px-6 py-10">
      <p className="font-semibold tracking-tight">
        RewardsPilot<span className="text-accent">OS</span>
      </p>

      <div className="mt-8 w-full max-w-xl rounded-2xl border border-neutral-800 bg-neutral-900/50 px-10 py-9 text-center">
        <div className="flex justify-center gap-1.5" aria-hidden="true">
          {Array.from({ length: STEPS }, (_, i) => (
            <span
              key={i}
              className={`h-[3px] w-9 rounded-full ${
                i < step ? "bg-accent" : "bg-neutral-800"
              }`}
            />
          ))}
        </div>
        <p className="mt-3 text-[11px] uppercase tracking-widest text-neutral-600 tabular-nums">
          {step} of {STEPS}
        </p>

        {step === 1 ? (
          <Step
            title="Let’s set up your wallet"
            lede="Tell us which cards you carry. Everything after this builds on it — and you can change it any time."
          >
            <div className="mt-6 grid gap-2 text-left">
              {KNOWN_CARDS.map((card) => {
                const on = picked.includes(card.label);
                return (
                  <button
                    key={card.label}
                    type="button"
                    aria-pressed={on}
                    onClick={() =>
                      setPicked(
                        on ? picked.filter((l) => l !== card.label) : [...picked, card.label]
                      )
                    }
                    className={`relative rounded-lg border px-4 py-3 text-left transition-colors ${
                      on
                        ? "border-accent bg-accent/10"
                        : "border-neutral-800 bg-neutral-900 hover:border-neutral-700"
                    }`}
                  >
                    <span className="block text-sm font-medium">{card.label}</span>
                    <span className="block text-xs text-neutral-400">{card.blurb}</span>
                    {on ? (
                      <span className="absolute right-4 top-1/2 -translate-y-1/2 rounded-full bg-accent px-1.5 text-[11px] text-white">
                        ✓
                      </span>
                    ) : null}
                  </button>
                );
              })}
            </div>
            <p className="mx-auto mt-5 max-w-sm text-xs leading-relaxed text-neutral-600">
              Only these three have verified reward rules today. Others can be tracked from
              Portfolio, but rewards can’t be calculated for them yet.
            </p>
          </Step>
        ) : null}

        {step === 2 ? (
          <Step
            title="How many points do you have?"
            lede="Roughly is fine. Without this we can say which card earns more, but not what you can actually book."
          >
            {created.length ? (
              <div className="mt-6 grid gap-2 text-left">
                {created.map((card) => (
                  <label
                    key={card.label}
                    className="flex items-center justify-between gap-4 rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-3"
                  >
                    <span className="text-sm">{card.label}</span>
                    <input
                      inputMode="numeric"
                      placeholder="0"
                      value={balances[card.label] ?? ""}
                      onChange={(e) =>
                        setBalances({ ...balances, [card.label]: e.target.value })
                      }
                      className="w-28 rounded border border-neutral-800 bg-neutral-950 px-2.5 py-1.5 text-right text-sm tabular-nums outline-none focus:border-accent"
                    />
                  </label>
                ))}
              </div>
            ) : (
              <p className="mt-6 text-sm text-neutral-500">No cards added — nothing to record.</p>
            )}
            <p className="mt-5 text-xs text-neutral-600">
              Leave blank to skip. You can update these whenever a statement arrives.
            </p>
          </Step>
        ) : null}

        {step === 3 ? (
          <Step
            title="You’re set up"
            lede="You can add travel preferences any time from Settings — we’ll ask when it actually changes an answer."
          >
            <div className="mx-auto mt-6 grid h-11 w-11 place-items-center rounded-full border border-emerald-800 bg-emerald-950/50 text-lg text-emerald-200">
              ✓
            </div>
            <p className="mt-4 text-sm text-neutral-400">
              {created.length} {created.length === 1 ? "card" : "cards"} added.
            </p>
          </Step>
        ) : null}

        {step === 4 ? (
          <Step title="Try asking" lede="This is what the app is for. Pick one, or write your own.">
            <div className="mt-6 grid gap-2 text-left">
              {[
                "Which of my cards is best for a ₹50,000 flight?",
                "What can I book with the points I have?",
                "How many points would a ₹20,000 hotel booking earn?",
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => router.push("/chat")}
                  className="rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-3 text-left text-sm text-neutral-300 hover:border-accent hover:text-neutral-100"
                >
                  {q}
                </button>
              ))}
            </div>
          </Step>
        ) : null}

        {error ? (
          <div className="mt-5 text-left">
            <ErrorNotice error={error} />
          </div>
        ) : null}

        <div className="mt-8 flex items-center gap-3 border-t border-neutral-800 pt-5">
          {step > 1 && step < 4 ? (
            <button
              onClick={() => setStep(step - 1)}
              className="rounded border border-neutral-800 px-3 py-1.5 text-xs text-neutral-300 hover:border-neutral-700"
            >
              Back
            </button>
          ) : null}
          <span className="flex-1" />
          {step < 4 ? (
            <button
              onClick={() => router.push("/chat")}
              className="text-xs text-neutral-500 hover:text-neutral-300"
            >
              Skip setup
            </button>
          ) : null}
          <button
            onClick={next}
            disabled={busy}
            className="rounded bg-accent px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {busy ? "Saving…" : step === 4 ? "Go to Ask" : step === 3 ? "Finish" : "Continue"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Step({
  title,
  lede,
  children,
}: {
  title: string;
  lede: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mt-6">
      <h1 className="text-balance text-2xl font-semibold tracking-tight">{title}</h1>
      <p className="mx-auto mt-3 max-w-sm text-sm leading-relaxed text-neutral-400">{lede}</p>
      {children}
    </div>
  );
}
