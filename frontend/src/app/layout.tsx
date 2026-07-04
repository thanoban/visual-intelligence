import type { Metadata } from "next";

import { SessionProvider } from "@/components/session-provider";

import "./globals.css";

export const metadata: Metadata = {
  title: "VisualSprint",
  description: "AI meeting intelligence for multilingual software teams.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
