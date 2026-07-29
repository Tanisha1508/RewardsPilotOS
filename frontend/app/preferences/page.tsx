"use client";

import { useEffect, useState } from "react";
import { api, ApiRequestError } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import { Empty, ErrorNotice, Shell, WakingNotice } from "@/components/shell";

// Preferences (BUILD_SPEC §10).
//
// These are not cosmetic settings. `RecallMemory` reads them and the Recommender
// puts them in its state digest, so they already shape the answers you get. And
// the `StorePreference` tool can WRITE one during a conversation — meaning the
// system could hold a durable opinion about you that you had no way to see,
// correct, or even know existed. That is the reason this page exists: not to add
// a capability, but to make an existing one inspectable.
//
// Deliberately a plain key/value editor rather than a curated form. The keys are
// open — the agent may store one this UI has never heard of — and a fixed form
// would hide exactly the preferences most worth seeing.

/** Keys the system is known to use, offered as suggestions only. Typing any
 *  other key is allowed: the store is open, and pretending otherwise would hide
 *  agent-written preferences, which are the ones worth surfacing. */
const KNOWN_KEYS = [
  "preferred_airline_program",
  "preferred_hotel_program",
  "preferred_redemption_channel",
  "home_airport",
];

export default function PreferencesPage() {
  const preferences = useApi(() => api.getPreferences());
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [newKey, setNewKey] = useState("");
  const [newValue, setNewValue] = useState("");
  const [error, setError] = useState<{ message: string; requestId?: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (preferences.data) setDraft({ ...preferences.data.values });
  }, [preferences.data]);

  const stored = preferences.data?.values ?? {};
  const dirty = Object.keys(draft).some((key) => draft[key] !== stored[key]);

  async function save(values: Record<string, string>) {
    setError(null);
    setSaving(true);
    setSaved(false);
    try {
      await api.setPreferences(values);
      preferences.reload();
      setSaved(true);
    } catch (caught) {
      setError(
        caught instanceof ApiRequestError
          ? { message: caught.message, requestId: caught.requestId }
          : { message: caught instanceof Error ? caught.message : "Request failed." }
      );
    } finally {
      setSaving(false);
    }
  }

  async function addPreference(event: React.FormEvent) {
    event.preventDefault();
    const key = newKey.trim();
    if (!key) return;
    await save({ [key]: newValue.trim() });
    setNewKey("");
    setNewValue("");
  }

  return (
    <Shell>
      <h1 className="text-lg font-semibold tracking-tight">Preferences</h1>
      <p className="mt-1 max-w-2xl text-sm text-neutral-400">
        These influence the recommendations you get. Some may have been recorded automatically from
        things you said in Ask — everything the system remembers about you is listed here.
      </p>

      {error ? (
        <div className="mt-4">
          <ErrorNotice error={error} />
        </div>
      ) : null}

      <section className="mt-6">
        {preferences.error ? (
          <ErrorNotice error={preferences.error} />
        ) : preferences.loading ? (
          preferences.slow ? (
            <WakingNotice context="Loading preferences" />
          ) : (
            <p className="text-sm text-neutral-500">Loading…</p>
          )
        ) : !Object.keys(stored).length ? (
          <Empty message="Nothing recorded yet. Add a preference below, or mention one in Ask." />
        ) : (
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase tracking-wide text-neutral-500">
              <tr>
                <th className="py-2">Preference</th>
                <th className="py-2">Value</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-900">
              {Object.keys(stored)
                .sort()
                .map((key) => (
                  <tr key={key}>
                    <td className="py-2 pr-4 align-middle font-mono text-xs text-neutral-400">
                      {key}
                    </td>
                    <td className="py-2">
                      <input
                        value={draft[key] ?? ""}
                        onChange={(e) => setDraft({ ...draft, [key]: e.target.value })}
                        className="w-full max-w-md rounded border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-sm outline-none focus:border-accent"
                      />
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        )}

        {dirty ? (
          <div className="mt-4 flex items-center gap-3">
            <button
              onClick={() => save(draft)}
              disabled={saving}
              className="rounded bg-accent px-3 py-2 text-sm font-medium disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save changes"}
            </button>
            <button
              onClick={() => setDraft({ ...stored })}
              className="text-sm text-neutral-500 hover:text-neutral-300"
            >
              Discard
            </button>
          </div>
        ) : saved ? (
          <p className="mt-4 text-sm text-emerald-400">Saved.</p>
        ) : null}
      </section>

      <section className="mt-10 border-t border-neutral-900 pt-6">
        <h2 className="text-sm font-medium text-neutral-300">Add a preference</h2>
        <form onSubmit={addPreference} className="mt-3 flex flex-wrap items-end gap-2">
          <label className="block text-xs text-neutral-500">
            Key
            <input
              list="known-preference-keys"
              value={newKey}
              onChange={(e) => setNewKey(e.target.value)}
              placeholder="preferred_airline_program"
              className="mt-1 w-64 rounded border border-neutral-800 bg-neutral-900 px-3 py-2 font-mono text-xs outline-none focus:border-accent"
            />
            <datalist id="known-preference-keys">
              {KNOWN_KEYS.map((key) => (
                <option key={key} value={key} />
              ))}
            </datalist>
          </label>
          <label className="block text-xs text-neutral-500">
            Value
            <input
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              placeholder="singapore_airlines_krisflyer"
              className="mt-1 w-72 rounded border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-accent"
            />
          </label>
          <button
            type="submit"
            disabled={saving || !newKey.trim()}
            className="rounded bg-accent px-3 py-2 text-sm font-medium disabled:opacity-50"
          >
            Add
          </button>
        </form>
      </section>

      {/* Honest about a gap rather than offering a button that half-works.
          `PUT /preferences` merges by design, so sending a subset cannot remove
          a key, and no delete endpoint exists. Adding one is an API-contract
          change (CLAUDE.md build constraints), so it waits for a spec decision
          instead of being invented here. */}
      {Object.keys(stored).length ? (
        <p className="mt-8 max-w-2xl text-xs text-neutral-600">
          Preferences can be changed but not yet removed — the API merges updates and has no delete.
          To neutralise one, clear its value and save.
        </p>
      ) : null}
    </Shell>
  );
}
