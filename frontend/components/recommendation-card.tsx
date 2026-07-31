"use client";

import { useState } from "react";
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
  points: "Earns",
  amount: "On spend",
  category: "Category",
  channel: "Booked",
  card_key: "Card",
  applied: "Rate applied",
  rate: "Rate",
  month: "Month",
  status: "Status",
  cap_applied: "Capped",
  points_before_cap: "Before the cap",
  cap_scope: "Cap applies to",
  tool: "Worked out by",
  from_currency: "From",
  to_currency: "To",
  ratio: "Ratio",
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

function formatValue(key: string, value: unknown, cardNames?: Record<string, string>): string | null {
  if (value === null || value === undefined || value === "") return null;
  if (key === "card_key" && typeof value === "string") {
    return cardNames?.[value] ?? prettyKey(value);
  }
  if (key === "amount" && typeof value === "number") return `₹${formatNumber(value)}`;
  if (NUMBER_FIELDS.has(key) && typeof value === "number") return formatNumber(value);
  if (key === "cap_applied") return value === true ? "yes" : null; // only worth saying when true
  if (typeof value === "boolean") return value ? "yes" : "no";
  if (typeof value === "string") {
    return ["category", "channel", "applied", "status"].includes(key) ? prettyKey(value) : value;
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

function orderedFields(calc: Record<string, unknown>): string[] {
  const known = FIELD_ORDER.filter((k) => k in calc);
  const rest = Object.keys(calc).filter((k) => !FIELD_ORDER.includes(k) && k !== "tool");
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
          <p className="text-sm font-medium leading-relaxed text-neutral-100">{body.decision}</p>
          <span
            className={`shrink-0 rounded-full border px-2 py-0.5 text-xs ${CONFIDENCE_STYLE[level]}`}
            title={body.confidence?.reason}
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
                .map((key) => [key, formatValue(key, calc[key], cardNames)] as const)
                .filter(([, shown]) => shown !== null);
              if (fields.length === 0) return null;
              return (
                <div
                  key={i}
                  className="flex flex-wrap gap-x-5 gap-y-1 rounded border border-neutral-800/70 bg-neutral-900/40 px-3 py-2 text-xs"
                >
                  {fields.map(([key, shown]) => (
                    <span key={key} className="whitespace-nowrap">
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
                <li key={i}>{step}</li>
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
