"use client";

import { useState } from "react";
import { currencyLabel, nameCurrencies } from "@/lib/display";
import type { FeedbackStatus, Recommendation } from "@/types/api";

// The hero component (BUILD_SPEC §10): decision on top, deterministic numbers
// table, expandable reasoning, citations footer with freshness badges,
// confidence chip, accept/reject/save. Every number shown comes from the
// engine-produced `calculations`/`citations` — the card renders, never computes.

const CONFIDENCE_STYLE: Record<string, string> = {
  high: "bg-emerald-900/50 text-emerald-200 border-emerald-800",
  medium: "bg-amber-900/40 text-amber-200 border-amber-800",
  low: "bg-neutral-800 text-neutral-300 border-neutral-700",
};

// ── The numbers table (A4, rewritten 2026-07-31) ────────────────────────────
//
// It used to render `Object.entries(calc).filter(...).slice(0, 5)` — a raw dump
// of whichever five keys happened to come first. Two things were wrong with it,
// and the second is not cosmetic:
//
//  1. The labels were field names. A cardholder read `card_key: axis_atlas`.
//  2. **`points` was never shown.** An EarnResult declares
//     card_key, amount, category, channel, month, status, points… — so the
//     five-field slice ran out exactly one field before the answer. A table
//     headed "Numbers used" was displaying only the inputs. Confirmed live on
//     2026-07-31: an answer whose prose said "1250.0 EDGE Miles" showed a table
//     with no number in it at all.
//
// So the fields are now named and ordered deliberately, with the earned figure
// first, and nothing is truncated.
//
// Formatting only — never arithmetic. `maximumFractionDigits: 20` is load-
// bearing: the engines' figures are quoted verbatim throughout this product,
// and a default-rounded `toLocaleString` would silently change one on screen.
// en-IN grouping is deliberate too (₹1,25,000, not ₹125,000).
const NUMBER_FIELDS = new Set(["points", "points_before_cap", "amount", "cap_points"]);

const FIELD_LABELS: Record<string, string> = {
  points: "You would earn",
  amount: "On spend",
  category: "Category",
  channel: "Booked",
  card_key: "Card",
  applied: "Using its",
  rate: "Rate",
  month: "For",
  status: "Status",
  cap_applied: "Capped",
  points_before_cap: "Before the cap",
  cap_scope: "Cap applies to",
  tool: "Worked out by",
  from_currency: "From",
  to_currency: "To",
  ratio: "Ratio",
  multiplier: "Bonus multiplier",
};

// Order the reader cares about, not declaration order. Anything unlisted keeps
// its place after these, so a new engine field appears rather than vanishing.
const FIELD_ORDER = [
  "card_key",
  "points",
  "amount",
  "category",
  "channel",
  "applied",
  "rate",
  "points_before_cap",
  "cap_applied",
  "cap_scope",
  "month",
  "status",
];

/** "axis_atlas" -> "Axis Atlas". Only a fallback: the real card name is passed
 *  in from the page when it has one, because no amount of prettifying turns
 *  "hdfc_infinia" into "HDFC Infinia". */
function prettyKey(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatNumber(value: number) {
  return value.toLocaleString("en-IN", { maximumFractionDigits: 20 });
}

// Engine figures are floats, so a recommendation's prose quotes them the way it
// received them: "this flight booking of 25000.0 ... earning 1250.0 points",
// beside a numbers table that correctly reads ₹25,000 and 1,250. The model is
// not at fault and must not be "fixed" in the prompt — it is obeying the rule
// that matters most here, which is to copy engine numbers rather than restate
// them. So the repair belongs at the last possible moment, on the way to the
// screen.
//
// The rule is deliberately narrow: only a run of digits ending in a decimal
// point followed by nothing but zeros. That token is always an engine float and
// never anything else — a year is written 2026, never 2026.0, and a rate of 2.5
// or a confidence of 0.9 has a non-zero decimal and is left exactly as it is.
// Regrouping every bare integer would have turned 2026 into 2,026.
//
// This changes how a number reads, never which number it is: 25000.0 and 25,000
// are the same value, and `validate_recommendation` already accepts either form
// (it strips commas before checking a prose number against the tool results).
// Nothing here rounds, and nothing here computes.
const ENGINE_FLOAT = /\d[\d,]*\.0+(?![\d])/g;

export function formatProse(text: string): string {
  const grouped = text.replace(ENGINE_FLOAT, (token) => {
    const whole = Number(token.replace(/,/g, ""));
    return Number.isFinite(whole) ? whole.toLocaleString("en-IN") : token;
  });
  // The other half of the same problem: engine vocabulary reaching a sentence.
  // "1,665 hdfc_reward_points" becomes "1,665 HDFC Reward Points".
  return nameCurrencies(grouped);
}

function formatValue(
  key: string,
  value: unknown,
  cardNames?: Record<string, string>,
  calc: Record<string, unknown> = {}
): string | null {
  if (value === null || value === undefined || value === "") return null;
  if (key === "card_key" && typeof value === "string") {
    return cardNames?.[value] ?? prettyKey(value);
  }
  if (key === "amount" && typeof value === "number") return `₹${formatNumber(value)}`;
  // "2026-07" is how the engine stores a month, not how anyone reads one.
  if (key === "month" && typeof value === "string" && /^\d{4}-\d{2}$/.test(value)) {
    const [year, mon] = value.split("-");
    const name = new Date(Number(year), Number(mon) - 1, 1).toLocaleString("en-IN", {
      month: "long",
    });
    return `${name} ${year}`;
  }
  // "Rate 2" and "Rate 5" side by side read as "the second card is 2.5x better".
  // They are 2 EDGE Miles per ₹100 and 5 HDFC points per ₹150 — different
  // denominators AND different currencies (A4). The bare number was not jargon,
  // it was misleading, so the rate is only ever shown as a whole phrase.
  if (key === "rate") {
    const rate = value as { value?: unknown; status?: string };
    if (typeof rate?.value !== "number") return null;
    const per = typeof calc.rate_per_amount === "number" ? calc.rate_per_amount : null;
    const unit = typeof calc.reward_currency === "string" ? currencyLabel(calc.reward_currency) : "points";
    // No denominator means no honest comparison, so say nothing rather than a
    // number a reader would compare against another card's.
    if (per === null) return null;
    const qualifier = rate.status === "verified" ? "" : ` (${rate.status ?? "unverified"})`;
    return `${formatNumber(rate.value)} ${unit} per ₹${formatNumber(per)}${qualifier}`;
  }
  if (key === "multiplier") {
    const m = value as { value?: unknown };
    const n = typeof m?.value === "number" ? m.value : typeof value === "number" ? value : null;
    return n === null ? null : `${formatNumber(n)}× the standard rate`;
  }
  if (NUMBER_FIELDS.has(key) && typeof value === "number") return formatNumber(value);
  if (key === "cap_applied") return value === true ? "yes" : null; // only worth saying when true
  if (typeof value === "boolean") return value ? "yes" : "no";
  if (typeof value === "string") {
    // The engine's own words for these two are not a cardholder's.
    if (key === "applied") return value === "accelerated" ? "bonus rate" : "standard rate";
    if (key === "channel") return value === "direct" ? "directly with the merchant" : prettyKey(value);
    return ["category", "status", "cap_scope"].includes(key) ? prettyKey(value) : value;
  }
  // A verified value: {value, status, source, confidence}. Previously dropped
  // entirely by a `typeof v !== "object"` filter, which is how the rate behind
  // every calculation stayed invisible.
  if (typeof value === "object") {
    const v = value as { value?: unknown; status?: string };
    if (v.value === null || v.value === undefined) {
      return v.status === "unverified" ? "not verified" : null;
    }
    const shown = typeof v.value === "number" ? formatNumber(v.value) : String(v.value);
    return v.status === "verified" ? shown : `${shown} (${v.status ?? "unverified"})`;
  }
  return String(value);
}

/** Internal bookkeeping a cardholder cannot act on. `rule_version` identifies a
 *  file in this repo, not anything checkable — the Sources footer is what makes
 *  an answer traceable for a reader.
 *
 *  The `_note` fields are excluded for a different reason: they are *prose*, and
 *  they are already guaranteed to be in the answer. `_required_statements` in
 *  the recommender forces the channel note, the expiry note and the margin
 *  caveat into the decision or reasoning, and `validate_recommendation` rejects
 *  output that omits them. Repeating a sentence here as though it were a data
 *  field said the same thing twice — and, being a sentence in a field slot,
 *  it is what pushed the page into horizontal scrolling (found 2026-07-31 at
 *  1254px wide inside a 1470px window). */
const NEVER_SHOWN = new Set([
  "tool",
  "rule_version",
  "rule_version_id",
  "sources",
  "channel_note",
  "expiry_note",
  "unknown_reasons",
  "no_transfer_data",
  // Folded into the rate phrase above; on their own they are noise.
  "rate_per_amount",
  "reward_currency",
]);

/** Long values must be allowed to wrap. `whitespace-nowrap` is right for
 *  "Earns 1,250" and catastrophic for a sentence. */
const WRAP_THRESHOLD = 24;

/** Fields worth showing only when they carry information.
 *
 *  Shown always, they are noise that buries the four numbers that matter. The
 *  test each one has to pass: does this value change what the reader should do,
 *  or warn them about something? `status: computed` says "nothing went wrong",
 *  which is the default and not worth a slot; `status: unknown` very much is. */
function carriesInformation(key: string, calc: Record<string, unknown>): boolean {
  const capped = calc.cap_applied === true;
  switch (key) {
    case "status":
      return calc.status !== "computed";
    case "points_before_cap":
      // Identical to `points` unless a cap actually bit.
      return capped && calc.points_before_cap !== calc.points;
    case "cap_scope":
    case "cap_applied":
      return capped;
    default:
      return true;
  }
}

function orderedFields(calc: Record<string, unknown>): string[] {
  const usable = (k: string) => !NEVER_SHOWN.has(k) && carriesInformation(k, calc);
  const known = FIELD_ORDER.filter((k) => k in calc && usable(k));
  const rest = Object.keys(calc).filter((k) => !FIELD_ORDER.includes(k) && usable(k));
  return [...known, ...rest];
}

export function RecommendationCard({
  rec,
  onFeedback,
  cardNames,
}: {
  rec: Recommendation;
  onFeedback?: (status: FeedbackStatus) => void;
  /** card_key -> the name the user gave the card. Optional: a stored answer
   *  may name a card the user has since deleted, and the calculation must still
   *  render. Falls back to a title-cased key. */
  cardNames?: Record<string, string>;
}) {
  const [showReasoning, setShowReasoning] = useState(false);
  const body = rec.recommendation;
  const level = body.confidence?.level ?? "low";

  return (
    <div className="rounded-lg border border-neutral-800 bg-neutral-900/50">
      <div className="border-b border-neutral-800 px-5 py-4">
        <div className="flex items-start justify-between gap-4">
          <p className="text-sm font-medium leading-relaxed text-neutral-100">
            {formatProse(body.decision)}
          </p>
          <span
            className={`shrink-0 rounded-full border px-2 py-0.5 text-xs ${CONFIDENCE_STYLE[level]}`}
            title={body.confidence?.reason ? formatProse(body.confidence.reason) : undefined}
          >
            {level} confidence
          </span>
        </div>
      </div>

      {body.calculations.length > 0 ? (
        <div className="border-b border-neutral-800 px-5 py-3">
          <p className="mb-2 text-xs uppercase tracking-wide text-neutral-500">
            How these numbers were worked out
          </p>
          <div className="space-y-2">
            {body.calculations.map((calc, i) => {
              const fields = orderedFields(calc)
                .map((key) => [key, formatValue(key, calc[key], cardNames, calc)] as const)
                // Typed predicate, not a plain filter: `formatValue` returns
                // null for "nothing worth showing", and TypeScript cannot see
                // that through the tuple without this.
                .filter((pair): pair is readonly [string, string] => pair[1] !== null);
              if (fields.length === 0) return null;
              return (
                <div
                  key={i}
                  className="flex flex-wrap gap-x-5 gap-y-1 rounded border border-neutral-800/70 bg-neutral-900/40 px-3 py-2 text-xs"
                >
                  {fields.map(([key, shown]) => (
                    <span
                      key={key}
                      className={shown.length > WRAP_THRESHOLD ? "break-words" : "whitespace-nowrap"}
                    >
                      <span className="text-neutral-500">{FIELD_LABELS[key] ?? prettyKey(key)}</span>{" "}
                      <span
                        className={
                          key === "points"
                            ? "font-medium tabular-nums text-neutral-100"
                            : "tabular-nums text-neutral-300"
                        }
                      >
                        {shown}
                      </span>
                    </span>
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      {body.reasoning.length > 0 ? (
        <div className="border-b border-neutral-800 px-5 py-3">
          <button
            onClick={() => setShowReasoning((s) => !s)}
            className="text-xs text-neutral-400 hover:text-neutral-200"
          >
            {showReasoning ? "▾ Hide reasoning" : "▸ Show reasoning"}
          </button>
          {showReasoning ? (
            <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-neutral-300">
              {body.reasoning.map((step, i) => (
                <li key={i}>{formatProse(step)}</li>
              ))}
            </ol>
          ) : null}
        </div>
      ) : null}

      {body.citations.length > 0 ? (
        <div className="border-b border-neutral-800 px-5 py-3">
          <p className="mb-2 text-xs uppercase tracking-wide text-neutral-500">Sources</p>
          <ul className="space-y-1">
            {body.citations.map((c, i) => (
              <li key={i} className="flex items-center gap-2 text-xs">
                <a
                  href={c.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="truncate text-accent hover:underline"
                >
                  {c.source_url.replace(/^https?:\/\//, "")}
                </a>
                {/* Freshness badge — how current the cited source is. */}
                <span className="shrink-0 rounded bg-neutral-800 px-1.5 py-0.5 text-neutral-400">
                  {c.last_changed}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {onFeedback ? (
        <div className="flex items-center gap-2 px-5 py-3">
          <FeedbackButton label="Accept" status="accepted" current={rec.status} onClick={onFeedback} />
          <FeedbackButton label="Save" status="saved" current={rec.status} onClick={onFeedback} />
          <FeedbackButton label="Reject" status="rejected" current={rec.status} onClick={onFeedback} />
          {rec.status !== "generated" && rec.status !== "viewed" ? (
            <span className="ml-auto text-xs text-neutral-500">Marked {rec.status}</span>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function FeedbackButton({
  label,
  status,
  current,
  onClick,
}: {
  label: string;
  status: FeedbackStatus;
  current: string;
  onClick: (status: FeedbackStatus) => void;
}) {
  const active = current === status;
  return (
    <button
      onClick={() => onClick(status)}
      className={`rounded border px-3 py-1 text-xs ${
        active
          ? "border-accent bg-accent/20 text-neutral-100"
          : "border-neutral-800 text-neutral-400 hover:text-neutral-200"
      }`}
    >
      {label}
    </button>
  );
}
