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
const nextConfig = {
  reactStrictMode: true,
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
