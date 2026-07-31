"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiRequestError } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import { getSupabase, isSupabaseConfigured } from "@/lib/supabase";
import { ErrorNotice, Shell, WakingNotice } from "@/components/shell";

// Account (BUILD_SPEC §10).
//
// Deliberately thin, and honest about why. Supabase and the OAuth provider own
// authentication, and there is no endpoint to change an email, name or password
// from inside the app — `GET /auth/me` is read-only. So this shows what is true
// and says where the rest lives, rather than rendering fields that cannot save.
//
// It is separate from Reward preferences on purpose: those change what the app
// recommends, which makes them product settings. This is identity.

export default function AccountPage() {
  const me = useApi(() => api.me());

  return (
    <Shell>
      <h1 className="text-lg font-semibold tracking-tight">Account</h1>
      <p className="mt-1 max-w-2xl text-sm text-neutral-400">Who you are signed in as.</p>

      <section className="mt-6 max-w-xl">
        {me.error ? (
          <ErrorNotice error={me.error} />
        ) : me.loading ? (
          me.slow ? (
            <WakingNotice context="Loading your account" />
          ) : (
            <p className="text-sm text-neutral-500">Loading…</p>
          )
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[32rem] text-sm">
            <tbody className="divide-y divide-neutral-900">
              <Row label="Email" value={me.data?.email ?? "—"} />
              {/* Unknown reads as unknown. A blank name is not "no name". */}
              <Row label="Name" value={me.data?.name || "not set"} />
              <Row label="Time zone" value={me.data?.timezone || "not set"} />
            </tbody>
            </table>
          </div>
        )}

        <p className="mt-6 text-xs text-neutral-500">
          Your email and password are managed by your sign-in provider, not here. Sign out from the
          Settings menu.
        </p>
      </section>

      <DeleteAccount email={me.data?.email ?? null} />
    </Shell>
  );
}

/** Delete everything this service holds about you (privacy audit P3).
 *
 *  Behind a disclosure, then behind typing your own email. Not friction for its
 *  own sake: the cascade reaches further than most people expect — cards,
 *  balances, goals, preferences, and every question ever asked — and an
 *  irreversible action that is one click away will eventually be clicked by
 *  accident.
 *
 *  The copy states what is deleted AND what is not. Implying a clean wipe would
 *  be the more comfortable lie: the Supabase auth identity survives, because
 *  removing it needs the service-role key this service deliberately does not
 *  hold. */
function DeleteAccount({ email }: { email: string | null }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<{ message: string; requestId?: string } | null>(null);

  const confirmed = Boolean(email) && typed.trim().toLowerCase() === email?.toLowerCase();

  async function remove() {
    setBusy(true);
    setError(null);
    try {
      await api.deleteAccount();
      // Sign out too: leaving a valid session pointing at deleted data would
      // make every page error until the token expired.
      if (isSupabaseConfigured()) await getSupabase().auth.signOut();
      router.replace("/login");
    } catch (caught) {
      setError(
        caught instanceof ApiRequestError
          ? { message: caught.message, requestId: caught.requestId }
          : { message: caught instanceof Error ? caught.message : "Request failed." }
      );
      setBusy(false);
    }
  }

  return (
    <section className="mt-12 max-w-xl border-t border-neutral-900 pt-6">
      <h2 className="text-sm font-medium text-neutral-300">Delete your data</h2>

      {!open ? (
        <>
          <p className="mt-1 text-xs text-neutral-500">
            Permanently removes your cards, balances, goals, preferences and every question you
            have asked.
          </p>
          <button
            onClick={() => setOpen(true)}
            className="mt-3 rounded border border-red-900 px-3 py-1.5 text-xs text-red-300 hover:bg-red-950/40"
          >
            Delete my data
          </button>
        </>
      ) : (
        <div className="mt-3 rounded border border-red-900 bg-red-950/20 p-4">
          <p className="text-sm text-neutral-200">This cannot be undone.</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-neutral-400">
            <li>Your cards, balances, goals and preferences</li>
            <li>Every question you have asked and every answer you were given</li>
          </ul>
          {/* The honest caveat. Saying "account deleted" while an auth identity
              survives would be a lie the user only discovers on next sign-in. */}
          <p className="mt-3 text-xs text-neutral-500">
            Your sign-in itself is held by {" "}
            <span className="text-neutral-400">your authentication provider</span> and is not
            removed here — signing in again would create a new, empty account.
          </p>

          {error ? (
            <div className="mt-3">
              <ErrorNotice error={error} />
            </div>
          ) : null}

          <label className="mt-4 block text-xs text-neutral-500">
            Type <span className="text-neutral-300">{email ?? "your email"}</span> to confirm
            <input
              value={typed}
              onChange={(e) => setTyped(e.target.value)}
              autoComplete="off"
              className="mt-1 w-full rounded border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm outline-none focus:border-red-700"
            />
          </label>

          <div className="mt-3 flex gap-2">
            <button
              onClick={remove}
              disabled={!confirmed || busy}
              className="rounded bg-red-900 px-3 py-2 text-sm font-medium text-red-100 disabled:opacity-40"
            >
              {busy ? "Deleting…" : "Delete everything"}
            </button>
            <button
              onClick={() => {
                setOpen(false);
                setTyped("");
                setError(null);
              }}
              className="rounded border border-neutral-800 px-3 py-2 text-sm text-neutral-300"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <tr>
      <td className="w-40 py-2.5 text-neutral-400">{label}</td>
      <td className="py-2.5">{value}</td>
    </tr>
  );
}
