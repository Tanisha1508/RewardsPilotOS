// API response types, hand-written to match the Pydantic schemas
// (BUILD_SPEC §3: no codegen dependency).
//
// These mirror `contracts/api/envelope.py` and `backend/schemas/`. Hand-written
// means they can drift, so the rule is: change a Pydantic DTO, change the type
// here in the same commit.

/** Mirrors `contracts/api/envelope.py`. Every response has this shape — both
 *  successes and failures — so a caller never branches on response structure. */
export interface Envelope<T> {
  data: T | null;
  error: ApiError | null;
  meta: Meta;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
}

export interface Meta {
  request_id: string;
  generated_at: string;
}

/** Mirrors `backend/schemas/identity.py::UserOut`. */
export interface User {
  user_id: string;
  email: string;
  name: string | null;
  timezone: string | null;
}

/** Mirrors `backend/schemas/portfolio.py::CardOut`. */
export interface Card {
  card_id: string;
  issuer: string;
  card_name: string;
  network: string;
  /** Links the card to the transfer graph. Required — a guessed value resolves
   *  to the wrong graph node instead of failing. */
  reward_currency: string;
  joining_date: string | null;
  annual_fee: number | null;
  renewal_date: string | null;
  status: string;
}

export type CardInput = Omit<Card, "card_id">;
export type CardPatch = Partial<CardInput>;

/** Mirrors `backend/schemas/portfolio.py::PortfolioOut`. */
export interface Portfolio {
  portfolio_id: string;
  portfolio_name: string;
  cards: Card[];
}

/** Mirrors `backend/schemas/portfolio.py::BalanceOut`.
 *  `last_updated` is shown in the UI, not hidden: balances are user-entered and
 *  can be stale (KNOWN_LIMITATIONS item 1), so how old the number is forms part
 *  of the answer. */
export interface RewardBalance {
  balance_id: string;
  card_id: string;
  reward_currency: string;
  current_balance: number;
  expiry_date: string | null;
  last_updated: string;
}

/** Mirrors `backend/schemas/portfolio.py::LoyaltyOut`. */
export interface LoyaltyAccount {
  loyalty_id: string;
  program_name: string;
  program_type: "airline" | "hotel";
  balance: number;
  status_tier: string | null;
  last_updated: string;
}

/** Mirrors `backend/schemas/identity.py::GoalOut`. */
export interface Goal {
  goal_id: string;
  goal_type: "trip" | "redemption" | "savings";
  description: string;
  target_date: string | null;
  status: string;
}

export interface Preferences {
  values: Record<string, string>;
}

export interface HealthReport {
  status: "ok" | "degraded";
  checks: Record<string, string>;
}
