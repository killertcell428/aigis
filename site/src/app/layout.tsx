import type { Metadata } from "next";
import "./globals.css";
import { LanguageProvider } from "@/contexts/LanguageContext";

export const metadata: Metadata = {
  title: {
    default: "Aigis — Open-source LLM Security Library | Protect Against Prompt Injection",
    template: "%s | Aigis",
  },
  description:
    "Open-source Python library to protect LLM apps from prompt injection, PII leaks, jailbreaks & SQL injection. OWASP LLM Top 10 coverage, zero dependencies. pip install pyaigis",
  keywords: [
    "LLM security",
    "prompt injection",
    "AI safety",
    "Python",
    "aigis",
    "guardrails",
    "OWASP LLM",
  ],
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
  openGraph: {
    title: "Aigis — Open-source LLM Security Library | Protect Against Prompt Injection",
    description:
      "Open-source Python library to protect LLM apps from prompt injection, PII leaks, jailbreaks & SQL injection. OWASP LLM Top 10 coverage, zero dependencies. pip install pyaigis",
    url: "https://aigis.dev",
    type: "website",
    images: [
      {
        url: "/og-image.svg",
        width: 1200,
        height: 630,
        alt: "Aigis — Open-source LLM Security Library",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Aigis — Open-source LLM Security Library | Protect Against Prompt Injection",
    description:
      "Open-source Python library to protect LLM apps from prompt injection, PII leaks, jailbreaks & SQL injection. OWASP LLM Top 10 coverage, zero dependencies.",
    images: ["/og-image.svg"],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <LanguageProvider>{children}</LanguageProvider>
      </body>
    </html>
  );
}
