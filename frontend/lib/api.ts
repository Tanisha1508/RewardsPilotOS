"use client";

import { getAccessToken } from "@/lib/supabase";
import type {
  Card,
  CardInput,
  CardPatch,
  Envelope,
  FeedbackStatus,
  Goal,
  GoalInput,
  GoalPatch,
  HealthReport,
  KnowledgeSearchResult,
  LoyaltyAccount,
  Portfolio,
  Preferences,
  Recommendation,
  RewardBalance,
  User,
} from "@/types/api";

// Typed fetch wrapper (BUILD_SPEC §10). Two things it refuses to do:
//
// 1. Return a partially-typed response. Every call unwraps the envelope and
//    either returns `data` or throws — callers never have to check `error`
//    themselves and never accidentally render an error body as data.
// 2. Send a request without a token to a protected route. The backend would
//    reject it anyway; failing here gives a better message than a bare 401.

// Relative, deliberately (2026-07-30). Every call now goes to this app's own
// origin and is forwarded to the backend by the rewrite in `next.config.mjs`.
//
// This was an absolute cross-origin URL until the frontend and backend became
// same-origin. Three things follow from the change, and the third is the reason
// for it:
//
//   - CORS stops applying, and with it the preflight round-trip on every
//     non-GET request. On a backend that sleeps after 15 minutes, one fewer
//     round-trip on the waking request is worth having.
//   - The backend's origin leaves the browser bundle, so `connect-src` can drop
//     it and the client no longer advertises where the API lives.
//   - It is the prerequisite for httpOnly cookie sessions (privacy audit P7).
//     A cookie set by this origin is a *third-party* cookie for a backend on
//     another registrable domain, and modern browsers block those by default.
//     Cookie auth is not a drop-in replacement for the token in localStorage —
//     it is impossible until the API is same-origin. This is that step.
//
// Note there is no `?? "http://localhost:8000"` fallback any more: in
// development the rewrite handles the hop too, so a relative path is correct
// everywhere and a default that silently bypasses the proxy would hide a
// misconfigured rewrite until production.
const BASE_URL = "";

export class ApiRequestError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly status: number,
    readonly requestId: string
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}

async function request<T>(
  path: string,
  options: { method?: string; body?: unknown; authenticated?: boolean } = {}
): Promise<T> {
  const { method = "GET", body, authenticated = true } = options;

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (authenticated) {
    const token = await getAccessToken();
    if (!token) {
      throw new ApiRequestError("not_signed_in", "You are not signed in.", 401, "");
    }
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });

  let envelope: Envelope<T>;
  try {
    envelope = (await response.json()) as Envelope<T>;
  } catch {
    // A non-envelope response means something upstream of the app answered —
    // a proxy, a gateway timeout. Say that rather than "undefined".
    throw new ApiRequestError(
      "malformed_response",
      `The server returned a non-JSON response (HTTP ${response.status}).`,
      response.status,
      ""
    );
  }

  if (!response.ok || envelope.error) {
    throw new ApiRequestError(
      envelope.error?.code ?? "unknown_error",
      envelope.error?.message ?? `Request failed with HTTP ${response.status}.`,
      response.status,
      envelope.meta?.request_id ?? ""
    );
  }

  return envelope.data as T;
}

export const api = {
  health: () => request<HealthReport>("/api/v1/health", { authenticated: false }),

  syncUser: (name?: string) =>
    request<User>("/api/v1/auth/sync", { method: "POST", body: { name: name ?? null } }),
  me: () => request<User>("/api/v1/auth/me"),
  // Erases everything this service holds about the caller. Scoped to the token's
  // own sub — no id parameter, so it cannot be aimed at anyone else. Does NOT
  // remove the Supabase auth identity.
  deleteAccount: () => request<{ deleted: boolean }>("/api/v1/auth/me", { method: "DELETE" }),

  getPortfolio: () => request<Portfolio>("/api/v1/portfolio"),
  listCards: () => request<Card[]>("/api/v1/portfolio/cards"),
  addCard: (card: CardInput) =>
    request<Card>("/api/v1/portfolio/cards", { method: "POST", body: card }),
  updateCard: (cardId: string, changes: CardPatch) =>
    request<Card>(`/api/v1/portfolio/cards/${cardId}`, { method: "PATCH", body: changes }),
  deleteCard: (cardId: string) =>
    request<{ id: string; deleted: boolean }>(`/api/v1/portfolio/cards/${cardId}`, {
      method: "DELETE",
    }),

  listBalances: () => request<RewardBalance[]>("/api/v1/portfolio/balances"),
  setBalance: (
    cardId: string,
    balance: { reward_currency: string; current_balance: number; expiry_date?: string | null }
  ) =>
    request<RewardBalance>(`/api/v1/portfolio/balances/${cardId}`, {
      method: "PUT",
      body: balance,
    }),

  listLoyalty: () => request<LoyaltyAccount[]>("/api/v1/portfolio/loyalty"),

  getPreferences: () => request<Preferences>("/api/v1/preferences"),
  setPreferences: (values: Record<string, string>) =>
    request<Preferences>("/api/v1/preferences", { method: "PUT", body: { values } }),

  // PUT merges, so it can set a key but never unset one — hence a separate
  // delete rather than "send an empty value".
  deletePreference: (key: string) =>
    request<{ key: string; deleted: boolean }>(
      `/api/v1/preferences/${encodeURIComponent(key)}`,
      { method: "DELETE" }
    ),

  listGoals: () => request<Goal[]>("/api/v1/goals"),
  createGoal: (goal: GoalInput) =>
    request<Goal>("/api/v1/goals", { method: "POST", body: goal }),
  updateGoal: (goalId: string, changes: GoalPatch) =>
    request<Goal>(`/api/v1/goals/${goalId}`, { method: "PATCH", body: changes }),
  deleteGoal: (goalId: string) =>
    request<{ goal_id: string; deleted: boolean }>(`/api/v1/goals/${goalId}`, {
      method: "DELETE",
    }),

  // Intelligence: chat runs the workflow and persists a recommendation.
  chat: (query: string) =>
    request<Recommendation>("/api/v1/chat", { method: "POST", body: { query } }),
  listRecommendations: () => request<Recommendation[]>("/api/v1/recommendations"),
  getRecommendation: (id: string) =>
    request<Recommendation>(`/api/v1/recommendations/${id}`),
  sendFeedback: (id: string, status: FeedbackStatus) =>
    request<Recommendation>(`/api/v1/recommendations/${id}/feedback`, {
      method: "POST",
      body: { status },
    }),

  searchKnowledge: (params: {
    q: string;
    issuer?: string;
    doc_type?: string;
    k?: number;
  }) => {
    const query = new URLSearchParams({ q: params.q });
    if (params.issuer) query.set("issuer", params.issuer);
    if (params.doc_type) query.set("doc_type", params.doc_type);
    if (params.k) query.set("k", String(params.k));
    return request<KnowledgeSearchResult>(`/api/v1/knowledge/search?${query.toString()}`);
  },
};
