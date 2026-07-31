import Link from "next/link";

// The privacy policy (privacy audit P5, written 2026-07-31).
//
// Deliberately NOT wrapped in `Shell`. Shell redirects anyone without a session
// to /login, and a privacy policy you can only read after signing up is not a
// privacy policy — this page has to be readable by someone deciding whether to
// sign up at all.
//
// Written in plain language on purpose. A policy nobody finishes reading fails
// at the only thing it is for, and this product's whole claim is that it does
// not assert things it cannot back up. That applies to its own policy first.
//
// The hard part of this page is section 3. Google's Gemini API terms say, of
// the free tier, that Google "uses the content you submit... to provide,
// improve, and develop Google products and services", that "human reviewers may
// read, annotate, and process your API input and output", and — plainly — "do
// not submit sensitive, confidential, or personal information to the Unpaid
// Services". This app runs on that free tier and sends card holdings and
// balances. Saying so is uncomfortable, which is exactly why it has to be here
// rather than in a footnote.

export const metadata = {
  title: "Privacy — RewardsPilotOS",
  description: "What this app stores, what leaves it, and how to delete it.",
};

const UPDATED = "31 July 2026";

export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-2xl px-5 py-10 sm:px-6 sm:py-14">
      {/* /chat rather than /login: reachable from the Settings menu now, and a
          signed-out visitor following it is redirected back to /login by the
          Shell guard anyway. One link that is correct from both directions. */}
      <Link href="/chat" className="text-sm text-accent-soft hover:underline">
        ← Back to the app
      </Link>

      <h1 className="mt-6 text-2xl font-semibold tracking-tight">Privacy</h1>
      <p className="mt-2 text-sm text-neutral-400">
        What this app stores, what leaves it, and how to get rid of it. Last updated {UPDATED}.
      </p>

      <Section title="1. What is stored">
        <p>Only what you enter, and what the app produces from it:</p>
        <List
          items={[
            "Your email address, from signing in.",
            "The cards you add — issuer, card name, network, and the reward programme.",
            "Point balances you record.",
            "Preferences and goals you set.",
            "Every question you ask and the answer you were given, with the numbers and sources used at the time.",
          ]}
        />
        <p>
          There is no tracking, no analytics, no advertising, and no third-party scripts of any kind
          in this app.
        </p>
      </Section>

      <Section title="2. What is not stored">
        <p>
          No card numbers, no CVVs, no expiry dates, no bank logins, no transaction history. The app
          never asks for them and there is nowhere to put them. It works from what a card{" "}
          <em>earns</em>, not from what you have spent.
        </p>
      </Section>

      <Section title="3. What is sent to Google, and what Google may do with it" flagged>
        <p>
          Answers are written by Google&apos;s Gemini model. To answer a question, the app sends
          Google your question, the cards and balances you have recorded, and your preferences.
        </p>
        <p>
          Before it is sent, the app removes account identifiers, and any email address, phone
          number or long card-like number found in what you typed.
        </p>
        <p className="font-medium text-neutral-200">
          This app uses Gemini&apos;s free tier. Google&apos;s terms for that tier say Google uses
          submitted content to improve and develop its products, and that human reviewers may read
          it. Google also says not to send personal information to the free tier.
        </p>
        <p>
          Your card holdings and balances are personal information. So this is a real limitation,
          not a formality, and you should know it before you type anything you would mind a stranger
          reading. Google&apos;s paid tier does not train on submitted content; this app does not use
          it.
        </p>
        <p className="text-neutral-400">
          If Gemini&apos;s daily allowance runs out, answers may instead be written by Groq, whose
          terms say it does not train on submitted content and does not retain it by default.
        </p>
      </Section>

      <Section title="4. Who else can see it">
        <p>
          Nobody. Your data is readable only by your own signed-in account. It is not shared, sold,
          or sent anywhere except as described in section 3.
        </p>
        <p>
          The database is hosted by Supabase and the app by Vercel and Render — they store the data
          in order to run the service, and do not use it for anything else.
        </p>
      </Section>

      <Section title="5. How long it is kept">
        <p>
          Until you delete it. Nothing expires on its own. Your question history stays until you
          remove it.
        </p>
      </Section>

      <Section title="6. Deleting everything">
        <p>
          <strong className="text-neutral-200">Account → Delete my data</strong> removes your cards,
          balances, preferences, goals, question history and the account row itself, immediately and
          permanently. There is no soft-delete and no recovery.
        </p>
        <p className="text-neutral-400">
          Two honest caveats. Your sign-in identity is held by Supabase&apos;s authentication system
          and is deleted separately — email{" "}
          <span className="text-neutral-300">tanishag1508@gmail.com</span> and it will be removed.
          And anything already sent to Google under section 3 is outside this app&apos;s reach; that
          is a consequence of the free tier, and another reason section 3 is worth reading.
        </p>
      </Section>

      <Section title="7. Contact">
        <p>
          This is a personal project, not a company. For anything at all —
          <span className="text-neutral-300"> tanishag1508@gmail.com</span>.
        </p>
      </Section>

      <p className="mt-10 border-t border-neutral-800 pt-5 text-xs text-neutral-600">
        If any of this stops being true, this page is wrong and should be fixed before the app is.
      </p>
    </main>
  );
}

function Section({
  title,
  children,
  flagged,
}: {
  title: string;
  children: React.ReactNode;
  flagged?: boolean;
}) {
  return (
    <section
      className={`mt-8 ${
        flagged ? "rounded-lg border border-amber-900/60 bg-amber-950/20 p-4 sm:p-5" : ""
      }`}
    >
      <h2 className="text-base font-medium text-neutral-100">{title}</h2>
      <div className="mt-2 space-y-3 text-sm leading-relaxed text-neutral-300">{children}</div>
    </section>
  );
}

function List({ items }: { items: string[] }) {
  return (
    <ul className="list-disc space-y-1 pl-5">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}
