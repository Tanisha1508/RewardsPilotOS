# ADR-018: Tiered LLM Fallback (Gemini models → Groq)

## Status

Accepted (2026-07-21). Extends the LLM configuration of BUILD_SPEC §1 / ADR-015.

**Amendment (2026-07-21).** Originally scoped to Gemini-only (two models). Extended
the same session, at the product owner's request and with a key supplied, to add
**Groq** as a cross-provider third tier — the "second free-tier provider"
alternative below, now implemented rather than deferred. Groq (free tier, open
models) is in-constraint; it is not Grok (xAI, paid), which stays rejected. The
Groq tier is inert until `GROQ_API_KEY` is set.

## Context

During D4, a live `/chat` call failed because `gemini-3.5-flash` returned
`503 UNAVAILABLE` ("This model is currently experiencing high demand"),
repeatedly, for several minutes. The workflow degraded correctly — planner
retried, recommender retried, then a clean `502 recommendation_unavailable`
with the reason — but the user got no answer for a transient, capacity-side
blip that had nothing to do with our data or code.

A single model is a single point of failure for exactly this class of outage.
The failure is not permanent (a retry minutes later succeeds) and not our fault
(Google-side capacity), so a same-model retry alone does not help while the
spike lasts.

Two constraints shape the fix:

- **Free tier / open source only** (CLAUDE.md hard rule #3). This rules out
  adding a paid provider — notably **Grok (xAI)**, which was asked about and is
  a paid API. (Grok ≠ Groq; Groq's free tier would be in-constraint, but a new
  *provider* is a larger stack decision — see Alternatives.)
- **The stack is locked to Gemini** (BUILD_SPEC §1). Staying within Gemini
  avoids a stack change while still adding real redundancy.

The insight that makes an in-Gemini fallback worthwhile: **different Gemini
models are separate capacity pools.** A 503 on `gemini-3.5-flash` does not imply
a 503 on `gemini-flash-latest` — both were proven working during D3 prep, both
free tier.

## Decision

`default_llm()` returns a `FallbackLLM` over an ordered, tiered list:

1. `GEMINI_MODEL` (ADR-015 pinned primary)
2. `gemini-flash-latest` (second Gemini model — separate capacity pool)
3. **Groq** `llama-3.3-70b-versatile` — appended only when `GROQ_API_KEY` is set.

Tiers 1–2 handle the common case (a per-model capacity spike). Tier 3 is a
*different provider*, so it survives a Gemini-wide outage that no same-provider
fallback can. `GroqClient` calls Groq's OpenAI-compatible REST endpoint with
`httpx` — no new SDK dependency, so no library added to the locked stack.
`FallbackLLM` implements the existing `LLM` Protocol, so the planner, recommender,
and workflow are unchanged — they still see a single `complete(system, user)`.

**Transient vs. permanent is the routing rule.** On a *transient* failure
(503/UNAVAILABLE, 429/RESOURCE_EXHAUSTED, timeout, overloaded, connection), the
fallback rolls to the next model. On a *permanent* failure (bad key, malformed
request) it stops immediately — a different model fails identically, so trying it
just wastes a call and delays the error. If every model fails, it raises
`LLMUnavailableError` carrying each model's reason.

**`GEMINI_MODEL` still chooses the primary**, so ADR-015's single-env-var swap is
intact. Changing the primary is still a one-line config change; the fallback
list is a short constant (`FALLBACK_MODELS`) in `agents/registry.py`.

The existing `complete_with_retry` (one retry with backoff per LLM node) sits on
top unchanged, so the layered behaviour is: primary → fallback, and if both are
transiently down, one backoff, then primary → fallback again.

## Consequences

**Positive.** A transient 503 on the pinned model no longer blocks a
recommendation when another free model has capacity — which is the exact outage
that motivated this. No provider added, no stack change, still free tier.

**A recommendation can now be produced by a different model than configured.**
For a system built on traceable, deterministic *numbers*, this is low-risk: the
LLM never does arithmetic (ADR-002) and every figure is copied verbatim from
engine results and validated (grounded-number check). The model affects prose
and tool-plan phrasing, not the numbers. Still, the fallback model is a current
Gemini flash model, kept close in behaviour to the primary on purpose.

**The fallback list is code, not env.** Unlike the primary (`GEMINI_MODEL`),
adding or reordering fallbacks is a one-line edit to `FALLBACK_MODELS`. Kept in
code because it is a small, rarely-changed resilience detail, not per-deploy
config.

**A Gemini-wide outage is now covered — when Groq is configured.** With
`GROQ_API_KEY` set, a total Gemini outage falls through to Groq (a different
provider on different infrastructure). Without the key, the chain is Gemini-only
and a Gemini-wide outage still degrades to the graceful 502. So the resilience
level is a deployment choice: set the key for cross-provider redundancy, leave it
unset for Gemini-only.

**A recommendation can now be produced by an open model on Groq**, not just
Gemini. Same reasoning as the cross-model case: the LLM never does arithmetic and
every number is engine-produced and validated, so provider choice affects prose,
not the figures. Groq is the last resort, reached only when all of Gemini is
transiently down.

## Alternatives considered

**Add Grok (xAI) as the fallback (the literal request).** Rejected: Grok is a
paid API, which violates the free-tier-only hard rule. Flagged rather than
silently substituted.

**Add a second free-tier provider (Groq free tier, or local Ollama).**
**Adopted** (amendment above): Groq is now tier 3, at the product owner's request.
It is in-constraint (free tier, open models) and covers a Gemini-wide outage a
same-provider fallback cannot. Called via `httpx` against Groq's OpenAI-compatible
endpoint, so no SDK is added to the locked stack; gated on `GROQ_API_KEY`, so it
is inert until configured. Ollama (local, OSS) remains a possible future tier for
fully-offline operation.

**Just add more retries / exponential backoff on one model.** Simpler, but a
multi-minute capacity spike outlasts a reasonable retry budget, so the request
still fails. Backoff is retained on top of the fallback, not instead of it.

**Leave the graceful 502 as the only behaviour.** Acceptable for a transient
blip, and it was the pre-decision state. Rejected because the fix is small,
in-constraint, and removes a visible failure with no downside to the numbers.
