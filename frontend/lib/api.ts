"use client";

import { getAccessToken } from "@/lib/supabase";
import type {
  Card,
  CardInput,
  CardPatch,
  Envelope,
  FeedbackStatus,
  Goal,
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

const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

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

  listGoals: () => request<Goal[]>("/api/v1/goals"),

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
