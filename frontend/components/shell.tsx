"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { getSupabase, isSupabaseConfigured } from "@/lib/supabase";

// The password flow awaits `/auth/sync` before redirecting, but an OAuth
// sign-in (Google) navigates away from /login, so its first landing here must
// create the local user row or every backend call fails with "no portfolio for
// user". Sync is idempotent; once per browser session is enough. The flag is
// cleared on sign-out so a different fresh user in the same tab still syncs.
const SYNCED_FLAG = "rp_synced";

// First-run gate. Checked once per browser session, not per navigation: it costs
// an API call, and someone who deliberately skips setup must not be dragged back
// to it on every click.
//
// Sits in Shell rather than on one page because every entry point lands
// somewhere different — password login goes to /chat, Google OAuth returns to
// whatever URL is configured in the Supabase dashboard. A gate on a single page
// would be silently bypassed by the other route.
const FIRSTRUN_FLAG = "rp_firstrun_checked";

// Four tabs, each answering one question the others do not:
//   Ask       — what should I do?
//   Portfolio — what do I hold?
//   Redeem    — what can I get?
//   History   — what was I told?
//
// This replaced seven. Dashboard and Cards both answered "what do I hold" and
// showed the same balances twice; Transfer answered a question users do not ask
// (it is now a personalised section of Redeem); Goals and Preferences were
// settings wearing tab clothing. Dashboard returns as "Today" when the
// opportunity engine gives it something to say — a nav slot before the content
// is backwards.
const NAV = [
  { href: "/chat", label: "Ask" },
  { href: "/portfolio", label: "Portfolio" },
  { href: "/redeem", label: "Redeem" },
  { href: "/recommendations", label: "History" },
];

// Reached from the Settings menu, not the tab bar. Reward preferences are set
// during onboarding and only corrected here, so they do not earn permanent
// space — but they stay one click away and clearly labelled, because the store
// is writable by tooling and a preference you cannot find is one you cannot
// correct.
const SETTINGS_LINKS = [
  { href: "/preferences", label: "Reward preferences" },
  { href: "/account", label: "Account" },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  // Auth guard. Every protected page wraps in Shell (and /login does not), so
  // this is the single choke point for "no session → /login". It must be
  // client-side: the Supabase session lives in localStorage, which a server
  // middleware never sees. Until the session is confirmed we render a quiet
  // placeholder rather than the shell — the pre-guard behaviour (page chrome
  // plus per-widget "not signed in" errors) read as a broken app.
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!isSupabaseConfigured()) {
      // The login page owns the "Supabase not configured" explanation.
      router.replace("/login");
      return;
    }
    const supabase = getSupabase();
    let cancelled = false;

    supabase.auth.getSession().then(({ data }) => {
      if (cancelled) return;
      if (data.session) {
        if (!sessionStorage.getItem(SYNCED_FLAG)) {
          // Fire-and-forget: a failed sync must not brick the page — the
          // per-widget errors already say what went wrong in that case.
          api
            .syncUser()
            .then(() => sessionStorage.setItem(SYNCED_FLAG, "1"))
            .catch(() => {});
        }
        setReady(true);

        // A brand-new account has nothing to show on any tab, so send it to
        // setup. Deliberately only when the list is *known* to be empty: a
        // failed or slow call must never look like "you have no cards" and
        // bounce someone out of the app they were using.
        if (!sessionStorage.getItem(FIRSTRUN_FLAG)) {
          api
            .listCards()
            .then((cards) => {
              sessionStorage.setItem(FIRSTRUN_FLAG, "1");
              if (!cancelled && cards.length === 0) router.replace("/welcome");
            })
            .catch(() => {});
        }
      } else {
        router.replace("/login");
      }
    });

    // Covers sign-out from another tab and session expiry mid-use, not just
    // the button below.
    const { data: sub } = supabase.auth.onAuthStateChange((event) => {
      if (event === "SIGNED_OUT") {
        sessionStorage.removeItem(SYNCED_FLAG);
        sessionStorage.removeItem(FIRSTRUN_FLAG);
        router.replace("/login");
      }
    });
    return () => {
      cancelled = true;
      sub.subscription.unsubscribe();
    };
  }, [router]);

  async function signOut() {
    if (isSupabaseConfigured()) await getSupabase().auth.signOut();
    router.push("/login");
  }

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-neutral-500">Checking session…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-neutral-800">
        <div className="mx-auto flex max-w-5xl items-center gap-6 px-6 py-4">
          <Link href="/chat" className="font-semibold tracking-tight">
            RewardsPilot<span className="text-accent">OS</span>
          </Link>
          <nav className="flex gap-5 text-sm">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={
                  pathname === item.href
                    ? "text-neutral-100"
                    : "text-neutral-400 hover:text-neutral-200"
                }
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="ml-auto">
            <SettingsMenu onSignOut={signOut} />
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-8">{children}</main>
    </div>
  );
}

/** The Settings menu.
 *
 *  Called "Settings", not "Account": it holds reward preferences, which change
 *  what the app recommends and are therefore product settings, not profile
 *  fields. Labelled in text rather than shown as a bare avatar — the first
 *  person to review the design went looking for it and could not find it. */
function SettingsMenu({ onSignOut }: { onSignOut: () => void }) {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  // Close on route change, so following a link does not leave the menu hanging.
  useEffect(() => setOpen(false), [pathname]);

  useEffect(() => {
    if (!open) return;
    const close = () => setOpen(false);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("click", close);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("click", close);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className="relative" onClick={(e) => e.stopPropagation()}>
      <button
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="true"
        className="flex items-center gap-1.5 text-sm text-neutral-400 hover:text-neutral-200"
      >
        Settings
        <span aria-hidden="true" className="text-xs">
          ⌄
        </span>
      </button>

      {open ? (
        <div className="absolute right-0 top-8 z-10 w-52 rounded-lg border border-neutral-800 bg-neutral-900 p-1.5 shadow-xl">
          {SETTINGS_LINKS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="block rounded px-2.5 py-1.5 text-sm text-neutral-300 hover:bg-neutral-800 hover:text-neutral-100"
            >
              {item.label}
            </Link>
          ))}
          <div className="my-1.5 h-px bg-neutral-800" />
          <button
            onClick={onSignOut}
            className="block w-full rounded px-2.5 py-1.5 text-left text-sm text-neutral-300 hover:bg-neutral-800 hover:text-neutral-100"
          >
            Sign out
          </button>
        </div>
      ) : null}
    </div>
  );
}

/** Renders an API failure without pretending it did not happen.
 *  The request id is shown because it is what makes a user-reported problem
 *  findable in the logs. */
export function ErrorNotice({ error }: { error: { message: string; requestId?: string } }) {
  return (
    <div className="rounded border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-200">
      <p>{error.message}</p>
      {error.requestId ? (
        <p className="mt-1 text-xs text-red-300/70">Request id: {error.requestId}</p>
      ) : null}
    </div>
  );
}

export function Empty({ message }: { message: string }) {
  return <p className="text-sm text-neutral-500">{message}</p>;
}

/** What leaves the service when you ask a question (privacy audit P5).
 *
 *  Answering a question sends the query, the cards and balances you have
 *  recorded, and your preferences to Google's Gemini API. A user had no way to
 *  know that, and no way to weigh it. Saying so is not optional politeness: the
 *  whole product rests on not asserting things that are not true, and silence
 *  about where financial data goes is the same failure in a different register.
 *
 *  Deliberately placed on Ask rather than buried in a policy page — it belongs
 *  where the sending happens, at the moment of choosing to send. Deliberately
 *  factual rather than reassuring: it names the recipient and the contents, and
 *  does not editorialise about safety.
 *
 *  Database identifiers are stripped before the request leaves (P2), which is
 *  worth stating because it is the one mitigation a reader cannot verify. */
export function DataNotice() {
  return (
    <p className="mt-2 text-xs leading-relaxed text-neutral-600">
      Answering uses Google Gemini. Your question, the cards and balances you have recorded, and
      your preferences are sent there; account identifiers are removed first. Answers are saved to
      your History until you delete them.
    </p>
  );
}

/** Shown when a request is still running after a few seconds.
 *
 *  The backend runs on a free tier that sleeps after ~15 minutes idle; the next
 *  request pays the wake-up (measured 15.6 s cold vs ~1.2 s warm). A bare
 *  "Loading…" through that reads as a hang, and the honest thing is to say
 *  which of the two is happening rather than let the user guess. */
export function WakingNotice({ context }: { context?: string }) {
  return (
    <p className="text-sm text-neutral-500">
      {context ?? "Loading"} — waking the server, which sleeps when idle. This can take up to a
      minute the first time.
    </p>
  );
}
