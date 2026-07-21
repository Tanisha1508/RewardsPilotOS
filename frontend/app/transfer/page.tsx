"use client";

import { useState } from "react";
import { api, ApiRequestError } from "@/lib/api";
import { Empty, ErrorNotice, Shell } from "@/components/shell";
import type { RetrievedChunk } from "@/types/api";

// Transfer explorer (BUILD_SPEC §10). Backed by the verified transfer_rules
// corpus via /knowledge/search — it shows the verified transfer-partner content
// with its source and freshness, scoped by issuer. It surfaces verified data,
// not model-computed paths; computed best-transfer-paths come through Ask/chat,
// which routes through the Graph Engine.

const ISSUERS = [
  { value: "", label: "All issuers" },
  { value: "hdfc", label: "HDFC" },
  { value: "axis", label: "Axis" },
  { value: "amex", label: "Amex" },
];

export default function TransferPage() {
  const [issuer, setIssuer] = useState("");
  const [query, setQuery] = useState("transfer partners and ratios");
  const [chunks, setChunks] = useState<RetrievedChunk[] | null>(null);
  const [error, setError] = useState<{ message: string; requestId?: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function search(event?: React.FormEvent) {
    event?.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await api.searchKnowledge({
        q: query.trim() || "transfer partners and ratios",
        issuer: issuer || undefined,
        doc_type: "transfer_rules",
        k: 8,
      });
      setChunks(result.chunks);
    } catch (caught) {
      setError(
        caught instanceof ApiRequestError
          ? { message: caught.message, requestId: caught.requestId }
          : { message: caught instanceof Error ? caught.message : "Request failed." }
      );
      setChunks(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Shell>
      <h1 className="text-lg font-semibold tracking-tight">Transfer explorer</h1>
      <p className="mt-1 text-sm text-neutral-400">
        Verified transfer-partner data by issuer, with sources. For a computed
        best-transfer path from your balances, use Ask.
      </p>

      <form onSubmit={search} className="mt-4 flex flex-wrap gap-2">
        <select
          value={issuer}
          onChange={(e) => setIssuer(e.target.value)}
          className="rounded border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-accent"
        >
          {ISSUERS.map((i) => (
            <option key={i.value} value={i.value}>
              {i.label}
            </option>
          ))}
        </select>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. airline partners, minimum transfer, removed partners"
          className="min-w-[16rem] flex-1 rounded border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-accent"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded bg-accent px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {busy ? "Searching…" : "Search"}
        </button>
      </form>

      <div className="mt-8 space-y-3">
        {error ? (
          <ErrorNotice error={error} />
        ) : chunks === null ? (
          <p className="text-sm text-neutral-600">Search to explore verified transfer data.</p>
        ) : chunks.length === 0 ? (
          <Empty message="No verified transfer data matched. Try a broader query." />
        ) : (
          chunks.map((chunk) => (
            <div
              key={`${chunk.doc_id}-${chunk.chunk_index}`}
              className="rounded border border-neutral-800 bg-neutral-900/40 px-4 py-3"
            >
              <div className="mb-1 flex items-center gap-2 text-xs">
                <span className="rounded bg-neutral-800 px-1.5 py-0.5 text-neutral-300">
                  {chunk.metadata.issuer}
                </span>
                <a
                  href={chunk.metadata.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="truncate text-accent hover:underline"
                >
                  {chunk.metadata.source_url.replace(/^https?:\/\//, "")}
                </a>
                <span className="ml-auto shrink-0 text-neutral-500">
                  {chunk.metadata.last_changed}
                </span>
              </div>
              <p className="whitespace-pre-line text-sm text-neutral-200">{chunk.content}</p>
            </div>
          ))
        )}
      </div>
    </Shell>
  );
}
