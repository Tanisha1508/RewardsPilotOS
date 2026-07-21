# ADR-015: Pin the Default Gemini Model to gemini-3.5-flash

## Status

Accepted (2026-07-21). Amends the model named in BUILD_SPEC §1 and CLAUDE.md.

> Numbered 015, not 014: ADR-014 is the Supabase asymmetric-JWT decision from
> the same sprint. The task that requested this ADR asked for "014"; that number
> was already taken, so this is 015.

## Context

BUILD_SPEC §1 pinned the default LLM to `gemini-2.0-flash`. A live probe of the
project's own `GEMINI_API_KEY` during D3 preparation — one real
`generate_content` call through the production `GeminiClient`, not a check that
the string was present — returned:

    429 RESOURCE_EXHAUSTED
    Quota exceeded for metric:
      generativelanguage.googleapis.com/generate_content_free_tier_requests,
      limit: 0, model: gemini-2.0-flash

The key authenticates. A 429 is *past* authentication — a bad key returns
`400 API_KEY_INVALID` or `403 PERMISSION_DENIED`. The signal that matters is
`limit: 0`: not usage exhausted for the day, but **no free-tier allocation at
all** for that model on a current account.

It is model-generational, confirmed by probing the account's model list:

| Model | Result |
|---|---|
| `gemini-2.0-flash`, `gemini-2.0-flash-001` | 429, `limit: 0` — no free quota |
| `gemini-2.5-flash`, `gemini-2.5-flash-lite` | 404 NOT_FOUND (listed, not serving generateContent) |
| `gemini-3.5-flash` | **works** — pinned, current |
| `gemini-flash-latest` | works — moving alias |

Google zeroed free-tier access to the 2.0 line as 2.5/3.x became current, so a
newly created account has no free `gemini-2.0-flash` quota. The default in the
spec had gone stale, and because the code only ever checked that the key string
existed (`/health` reported `llm: ok_configured` without ever calling Google),
nothing surfaced it until the first real request — which, on the current wiring,
would have been the first D4 recommendation.

## Decision

Change the default model to **`gemini-3.5-flash`** in every governed location:

- `backend/config/settings.py` (`Settings.gemini_model`)
- `agents/registry.py` (`GeminiClient` env fallback)
- BUILD_SPEC §1 (stack table) and §12 (env-var block)
- CLAUDE.md (stack note)
- `.env.example`, and `agents/workflows/demo.py`'s print fallback, for
  consistency — a stale value in either would contradict the rest

`.env` already carried `gemini-3.5-flash` from the diagnostic run; this brings
the committed defaults in line with it.

**Pin the version, do not use `gemini-flash-latest`.** The moving alias also
works today and would auto-follow Google's current flash model, but auto-follow
is the wrong default for this system. RewardsPilotOS is built on deterministic,
traceable outputs: the LLM never does arithmetic, every number is copied
verbatim from engine results, and recommendations are validated against grounded
tool output. A silently changing model can shift phrasing, formatting, and
instruction-following underneath that validation with no signal and no commit —
unannounced drift on the one non-deterministic component in a system whose whole
premise is traceability. A pinned model fails the opposite way: loudly and at a
known point, when Google eventually deprecates it, with a clear error and a
one-line fix. Loud-and-eventual beats silent-and-any-time here.

## Consequences

**Positive.** The default now works on a current account. The failure mode is
explicit: when `gemini-3.5-flash` is deprecated, calls fail with a clear model
error rather than degrading quietly.

**A manual bump is now owed on Google's deprecation schedule.** Pinning trades
auto-follow for a periodic one-line change to `GEMINI_MODEL`. That is the
intended trade — see the decision.

**The escape hatch is unchanged.** BUILD_SPEC §1 still makes the model swappable
through the single `GEMINI_MODEL` env var, and `.env` overrides the default with
no code change. An operator on a different account, region, or quota tier sets
that variable; this ADR only moves the fallback the variable overrides.

**No behavioural change to the engines.** This is a settings-only change. The
Rule Engine, Graph Engine, and retrieval do no LLM calls, so rules, graph, and
end-to-end evals are unaffected — re-run to confirm, not because a regression is
expected but because "settings-only" is a claim worth checking.

## Alternatives considered

**Use the moving alias `gemini-flash-latest`.** Rejected. It works today and
removes the future manual bump, but unannounced model drift is a worse failure
mode than an explicit, loud failure for a system built on deterministic,
traceable outputs. See the decision.

**Leave the spec at `gemini-2.0-flash` and only set `.env`.** Rejected. It
leaves the committed default broken for the next person, who gets `limit: 0`
with no explanation, and leaves the spec asserting something the platform no
longer offers for free.

**Enable billing to restore `gemini-2.0-flash` quota.** Rejected. The project is
free-tier-only by constraint (CLAUDE.md), and paying to keep an older model is
the wrong direction when a current model is free.
