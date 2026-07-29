"use client";

import Link from "next/link";

// First run (2026-07-29).
//
// Every entry point — signup, login, Google OAuth — lands on /dashboard, which
// for a new account rendered "0 / 0 / 0" and an empty table. Technically
// accurate, and useless: nothing said what the product does or what to do next.
//
// Shown INSTEAD of the empty stats rather than above them. Three zeroes are not
// information for someone who has not entered anything yet; they are noise
// competing with the one thing that matters.
//
// Deliberately one primary action. The steps below it are context, not a
// checklist to work through — a new user needs to know where to start, not
// everything the product can eventually do.

const STEPS = [
  {
    title: "Add your cards",
    body: "Ask compares only the cards you list. Three are supported today — one click each.",
  },
  {
    title: "Record what you hold",
    body: "Points balances turn “which card earns more” into “what can I actually book”.",
  },
  {
    title: "Ask a question",
    body: "“Which of my cards is best for a ₹50,000 flight?” — with the numbers and sources behind it.",
  },
];

export function FirstRun() {
  return (
    <section className="mt-6 rounded-lg border border-neutral-800 bg-neutral-900/40 px-6 py-6">
      <h2 className="text-base font-semibold tracking-tight">Let’s set up your wallet</h2>
      <p className="mt-1 max-w-xl text-sm text-neutral-400">
        RewardsPilotOS works out which of your cards to use for a purchase, and what your points are
        worth — from verified issuer terms, never guesses.
      </p>

      <Link
        href="/cards"
        className="mt-5 inline-block rounded bg-accent px-4 py-2 text-sm font-medium"
      >
        Add your first card
      </Link>

      <ol className="mt-6 grid gap-4 sm:grid-cols-3">
        {STEPS.map((step, i) => (
          <li key={step.title}>
            <p className="text-xs font-medium text-neutral-300">
              <span className="mr-1.5 text-neutral-600">{i + 1}</span>
              {step.title}
            </p>
            <p className="mt-1 text-xs leading-relaxed text-neutral-500">{step.body}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
