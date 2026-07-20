"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { getSupabase, isSupabaseConfigured } from "@/lib/supabase";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/cards", label: "Cards" },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  async function signOut() {
    if (isSupabaseConfigured()) await getSupabase().auth.signOut();
    router.push("/login");
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-neutral-800">
        <div className="mx-auto flex max-w-5xl items-center gap-6 px-6 py-4">
          <Link href="/dashboard" className="font-semibold tracking-tight">
            RewardsPilot<span className="text-accent">OS</span>
          </Link>
          <nav className="flex gap-4 text-sm">
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
          <button
            onClick={signOut}
            className="ml-auto text-sm text-neutral-400 hover:text-neutral-200"
          >
            Sign out
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-8">{children}</main>
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
