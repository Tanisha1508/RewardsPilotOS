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
// Origins this app legitimately talks to. Derived from the same env vars the
// client uses, so the policy cannot drift from the configuration: if the API
// moves and this is not updated, the app fails visibly rather than quietly
// shipping a policy that permits the wrong host.
const connectOrigins = [process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.NEXT_PUBLIC_API_URL]
  .filter(Boolean)
  .map((url) => new URL(url).origin);

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
  "img-src 'self' data: https:",
  "font-src 'self' data:",
  `connect-src 'self' ${connectOrigins.join(" ")}`.trim(),
  // No embedding: this app shows one person's finances, and clickjacking it
  // into an invisible frame is the cheapest attack there is.
  "frame-ancestors 'none'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

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
