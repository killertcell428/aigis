import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aigis",
  description: "AI Security Filter SaaS — Human-in-the-Loop LLM proxy",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gd-deep text-gd-text-primary">
        {children}
      </body>
    </html>
  );
}
