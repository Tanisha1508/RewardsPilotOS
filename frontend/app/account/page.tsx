"use client";

import { api } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
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
          <table className="w-full text-sm">
            <tbody className="divide-y divide-neutral-900">
              <Row label="Email" value={me.data?.email ?? "—"} />
              {/* Unknown reads as unknown. A blank name is not "no name". */}
              <Row label="Name" value={me.data?.name || "not set"} />
              <Row label="Time zone" value={me.data?.timezone || "not set"} />
            </tbody>
          </table>
        )}

        <p className="mt-6 text-xs text-neutral-500">
          Your email and password are managed by your sign-in provider, not here. Sign out from the
          Settings menu.
        </p>
      </section>
    </Shell>
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
