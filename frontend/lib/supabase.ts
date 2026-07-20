"use client";

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

// Supabase owns authentication; the backend only verifies the JWT it issues
// (BUILD_SPEC §1). The anon key is public by design — it is safe in the browser
// precisely because row access is governed server-side. The JWT *secret* and
// the service-role key must never appear in this bundle.

let client: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient {
  if (client) return client;

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!url || !anonKey) {
    // Fail loudly at the call site rather than constructing a client that
    // silently rejects every request with an opaque error.
    throw new Error(
      "Supabase is not configured: set NEXT_PUBLIC_SUPABASE_URL and " +
        "NEXT_PUBLIC_SUPABASE_ANON_KEY (see frontend/.env.local.example)."
    );
  }

  client = createClient(url, anonKey);
  return client;
}

export function isSupabaseConfigured(): boolean {
  return Boolean(
    process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  );
}

/** The access token for the current session, or null when signed out. */
export async function getAccessToken(): Promise<string | null> {
  if (!isSupabaseConfigured()) return null;
  const { data } = await getSupabase().auth.getSession();
  return data.session?.access_token ?? null;
}
