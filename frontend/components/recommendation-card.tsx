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

export function RecommendationCard({
  rec,
  onFeedback,
}: {
  rec: Recommendation;
  onFeedback?: (status: FeedbackStatus) => void;
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
            Numbers used (from the rule &amp; graph engines)
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <tbody className="divide-y divide-neutral-900">
                {body.calculations.map((calc, i) => (
                  <tr key={i}>
                    {Object.entries(calc)
                      .filter(([, v]) => v !== null && typeof v !== "object")
                      .slice(0, 5)
                      .map(([k, v]) => (
                        <td key={k} className="py-1 pr-4 align-top">
                          <span className="text-neutral-500">{k}:</span>{" "}
                          <span className="tabular-nums text-neutral-200">{String(v)}</span>
                        </td>
                      ))}
                  </tr>
                ))}
              </tbody>
            </table>
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
