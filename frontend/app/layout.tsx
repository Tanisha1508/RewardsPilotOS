import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RewardsPilotOS",
  description: "Credit card rewards copilot — every number traceable to a verified source.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
