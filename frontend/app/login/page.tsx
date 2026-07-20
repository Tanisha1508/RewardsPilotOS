"use client";

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
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const configured = isSupabaseConfigured();

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);
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
      router.push("/dashboard");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Sign-in failed.");
    } finally {
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
        <input
          type="password"
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="w-full rounded border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-accent"
        />
        <button
          type="submit"
          disabled={busy || !configured}
          className="w-full rounded bg-accent px-3 py-2 text-sm font-medium disabled:opacity-50"
        >
          {busy ? "Working…" : mode === "sign-in" ? "Sign in" : "Sign up"}
        </button>
      </form>

      {error ? <p className="mt-3 text-sm text-red-300">{error}</p> : null}
      {notice ? <p className="mt-3 text-sm text-neutral-300">{notice}</p> : null}

      <button
        onClick={() => setMode(mode === "sign-in" ? "sign-up" : "sign-in")}
        className="mt-4 text-xs text-neutral-500 hover:text-neutral-300"
      >
        {mode === "sign-in" ? "Need an account? Sign up" : "Already have an account? Sign in"}
      </button>
    </div>
  );
}
