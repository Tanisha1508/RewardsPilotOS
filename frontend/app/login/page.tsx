"use client";

import Link from "next/link";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { getSupabase, isSupabaseConfigured } from "@/lib/supabase";

// Login is Supabase's job (BUILD_SPEC §1): the client signs in, Supabase issues
// the JWT, and the backend only verifies it. After sign-in we call
// `/api/v1/auth/sync` to create or refresh the local user row — it is idempotent,
// so calling it on every login is correct rather than wasteful.

type Mode = "sign-in" | "sign-up";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("sign-in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  // Sign-up only. A password you cannot see, typed once, with no way to check it
  // — the two ways out of a typo are a reset email or losing the account, and
  // this page offered neither. One toggle covers both fields: hiding the
  // confirmation while revealing the password would defeat the point of each.
  const [confirm, setConfirm] = useState("");
  const [reveal, setReveal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const configured = isSupabaseConfigured();
  const signingUp = mode === "sign-up";

  /** Everything typed is cleared when the mode changes. A confirmation left
   *  behind from an abandoned sign-up is invisible on the sign-in form and would
   *  come back on the next switch. */
  function switchMode() {
    setMode(signingUp ? "sign-in" : "sign-up");
    setPassword("");
    setConfirm("");
    setReveal(false);
    setError(null);
    setNotice(null);
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);

    // Checked here rather than by the server: Supabase never sees the
    // confirmation, and a mismatch is not a failed sign-up — it is a typo, and
    // saying so without a round-trip keeps what was typed on screen.
    if (signingUp && password !== confirm) {
      setError("Those two passwords are not the same.");
      return;
    }

    setBusy(true);
    try {
      const supabase = getSupabase();
      const { data, error: authError } =
        mode === "sign-in"
          ? await supabase.auth.signInWithPassword({ email, password })
          : await supabase.auth.signUp({ email, password });

      if (authError) throw new Error(authError.message);

      // Sign-up with email confirmation returns no session yet. Say so instead
      // of redirecting to a dashboard that would immediately bounce back.
      if (!data.session) {
        setNotice("Check your email to confirm your account, then sign in.");
        return;
      }

      await api.syncUser();
      router.push("/chat");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Sign-in failed.");
    } finally {
      setBusy(false);
    }
  }

  async function signInWithGoogle() {
    setError(null);
    setNotice(null);
    setBusy(true);
    try {
      // Supabase drives the OAuth dance and redirects back to the app with a
      // session. `/auth/sync` cannot run here — the browser leaves this page —
      // so Shell's guard performs it on arrival (idempotent by design).
      const { error: authError } = await getSupabase().auth.signInWithOAuth({
        provider: "google",
        options: { redirectTo: `${window.location.origin}/chat` },
      });
      if (authError) throw new Error(authError.message);
      // On success the browser navigates away; nothing more to do here.
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Google sign-in failed.");
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-6">
      <h1 className="text-xl font-semibold tracking-tight">
        RewardsPilot<span className="text-accent">OS</span>
      </h1>
      <p className="mt-1 text-sm text-neutral-400">
        {mode === "sign-in" ? "Sign in to your portfolio." : "Create an account."}
      </p>

      {!configured ? (
        <div className="mt-6 rounded border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-200">
          Supabase is not configured. Set <code>NEXT_PUBLIC_SUPABASE_URL</code> and{" "}
          <code>NEXT_PUBLIC_SUPABASE_ANON_KEY</code> (see{" "}
          <code>frontend/.env.local.example</code>).
        </div>
      ) : null}

      <form onSubmit={submit} className="mt-6 space-y-3">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          className="w-full rounded border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-accent"
        />
        <div className="relative">
          <input
            type={reveal ? "text" : "password"}
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            autoComplete={signingUp ? "new-password" : "current-password"}
            className="w-full rounded border border-neutral-800 bg-neutral-900 py-2 pl-3 pr-16 text-sm outline-none focus:border-accent"
          />
          {/* `type="button"` matters: a bare button inside a form submits it, so
              revealing the password would have attempted a sign-in. */}
          <button
            type="button"
            onClick={() => setReveal((on) => !on)}
            aria-pressed={reveal}
            aria-label={reveal ? "Hide password" : "Show password"}
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded px-2 py-1 text-xs text-neutral-500 hover:text-neutral-200"
          >
            {reveal ? "Hide" : "Show"}
          </button>
        </div>

        {signingUp ? (
          <>
            <input
              type={reveal ? "text" : "password"}
              required
              minLength={8}
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="Confirm password"
              autoComplete="new-password"
              className="w-full rounded border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-accent"
            />
            <p className="text-xs text-neutral-600">At least 8 characters.</p>
          </>
        ) : null}

        <button
          type="submit"
          disabled={busy || !configured}
          className="w-full rounded bg-accent px-3 py-2 text-sm font-medium disabled:opacity-50"
        >
          {busy ? "Working…" : signingUp ? "Create account" : "Sign in"}
        </button>
      </form>

      <div className="mt-4 flex items-center gap-3 text-xs text-neutral-600">
        <div className="h-px flex-1 bg-neutral-800" />
        or
        <div className="h-px flex-1 bg-neutral-800" />
      </div>

      <button
        onClick={signInWithGoogle}
        disabled={busy || !configured}
        className="mt-4 w-full rounded border border-neutral-700 px-3 py-2 text-sm font-medium text-neutral-200 hover:border-neutral-500 disabled:opacity-50"
      >
        Continue with Google
      </button>

      {error ? <p className="mt-3 text-sm text-red-300">{error}</p> : null}
      {notice ? <p className="mt-3 text-sm text-neutral-300">{notice}</p> : null}

      <button onClick={switchMode} className="mt-4 text-xs text-neutral-500 hover:text-neutral-300">
        {signingUp ? "Already have an account? Sign in" : "Need an account? Sign up"}
      </button>

      {/* Before the decision, not after it. DPDP requires notice *before*
          processing, and someone signing up should be able to read what happens
          to their data without first handing it over. The page deliberately
          sits outside the auth guard for the same reason. */}
      <p className="mt-6 text-center text-xs text-neutral-600">
        How your data is handled:{" "}
        <Link href="/privacy" className="underline hover:text-neutral-400">
          Privacy
        </Link>
        .
      </p>
    </div>
  );
}
