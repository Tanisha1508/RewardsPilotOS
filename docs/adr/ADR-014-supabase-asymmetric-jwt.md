# ADR-014: Verify Supabase Tokens Against JWT Signing Keys, Not Only the Legacy Secret

## Status

Accepted (2026-07-20). Amends the auth assumption in BUILD_SPEC §12.

## Context

BUILD_SPEC §12 lists `SUPABASE_JWT_SECRET` for "backend verification", and D2
implemented exactly that: HS256 against a shared secret. That was Supabase's
scheme when the spec was written.

Supabase projects now migrate to **JWT Signing Keys** — asymmetric ES256 over
P-256, with public keys published at
`<project>/auth/v1/.well-known/jwks.json`. After migration the project signs
access tokens with the new key and keeps the legacy secret only to verify
tokens issued before the switch. With a one-hour access-token lifetime, those
are gone within the hour.

This project's own Supabase instance had already migrated. Its JWKS endpoint
publishes a single ES256 key, and the dashboard lists the legacy HS256 secret
as the *previous* key. An HS256-only backend would therefore have rejected
**every** real login — not intermittently, but universally, with a generic
401 that looks like a bad password.

The spec is not wrong so much as overtaken. Both schemes are live in the wild:
a project created before the migration still uses the shared secret.

## Decision

Support both, and let the token's `alg` header select the key source:

    HS256  -> SUPABASE_JWT_SECRET       (legacy projects)
    ES256  -> JWKS public key by `kid`  (migrated projects)

`SUPABASE_URL` already exists in the spec'd environment and is enough to derive
the JWKS URL, so no new environment variable is introduced.

**Reading `alg` before verifying is the dangerous part, and is handled
explicitly.** The header is attacker-controlled, which is the root of
algorithm-confusion attacks. Two properties contain it:

1. `ALLOWED_ALGORITHMS` is a closed allowlist. `none` is rejected; so is
   `RS256`, which is a perfectly good algorithm that this project does not use
   — the list is "what we accept", not "what looks asymmetric".
2. The two schemes never share key material. HS256 is verified **only** against
   `SUPABASE_JWT_SECRET`, never against a key retrieved from JWKS. The classic
   attack — sign HS256 using the public key as the HMAC secret — requires the
   server to feed a public key into HMAC, which no path does.

Both properties are tested, including a hand-assembled forgery, because PyJWT
refuses to *encode* that attack and a test that cannot construct it proves
nothing.

**Key rotation is transparent.** `PyJWKClient` caches keys and refetches when a
token presents an unknown `kid`, so a rotation does not require a redeploy.

## Consequences

**Positive.** Login works against a current Supabase project, and continues to
work against a legacy one. Rotation needs no configuration change.

**A network dependency on the auth path.** Verifying an ES256 token requires
the JWKS document. It is cached after the first fetch, but the first request
after a restart — or after a rotation — makes an outbound call, and a JWKS
endpoint that cannot be reached fails closed with a 401 rather than admitting
the token.

**`SUPABASE_JWT_SECRET` becomes conditional.** For a migrated project it can be
left unset; the error message says which scheme a token used and which value is
missing, since "unauthorized" would otherwise be indistinguishable from a
misconfigured server.

## Alternatives rejected

**Keep HS256 only and tell the operator to use the legacy secret.** The
dashboard describes the legacy secret as verify-only for already-issued tokens.
Building on a deprecated path that already fails is not a simplification.

**Fetch JWKS once at startup.** A rotation would then break every login until
the next deploy, and rotation is a routine security operation.

**Disable JWT signing keys in the Supabase project to match the spec.**
Downgrading a security posture to avoid a code change, on a project whose
governing rule is that correctness beats convenience.
