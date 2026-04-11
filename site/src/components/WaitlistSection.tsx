"use client";

import { useState } from "react";

const copy = {
  en: {
    heading: "Join the Waitlist for SaaS Dashboard (Beta)",
    subheading:
      "Get early access to the Aigis cloud dashboard — centralized threat monitoring, analytics, and team management.",
    placeholder: "you@company.com",
    button: "Join Waitlist",
    buttonLoading: "Joining...",
    success: "You're on the list! We'll reach out when beta opens.",
    error: "Something went wrong. Please try again.",
    disclaimer: "No spam. Unsubscribe anytime.",
  },
  ja: {
    heading: "SaaS ダッシュボード β版 ウェイトリスト登録",
    subheading:
      "Aigis クラウドダッシュボードへの早期アクセスを取得 — 脅威の一元監視・アナリティクス・チーム管理機能を先行体験。",
    placeholder: "you@company.com",
    button: "ウェイトリストに登録",
    buttonLoading: "登録中...",
    success: "登録完了！β版公開時にご連絡します。",
    error: "エラーが発生しました。もう一度お試しください。",
    disclaimer: "スパムなし。いつでも登録解除できます。",
  },
} as const;

interface WaitlistSectionProps {
  lang?: "en" | "ja";
}

export default function WaitlistSection({ lang = "en" }: WaitlistSectionProps) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const c = copy[lang];

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!email.trim()) return;

    setStatus("loading");
    try {
      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, lang }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setStatus("success");
    } catch {
      console.error("[WaitlistSection] Waitlist signup failed");
      setStatus("error");
    }
  };

  return (
    <section id="waitlist" className="relative bg-gradient-to-b from-guardian-800 to-guardian-950 py-20 overflow-hidden scroll-mt-16">
      {/* subtle grid overlay */}
      <div
        className="absolute inset-0 opacity-5"
        style={{
          backgroundImage:
            "linear-gradient(to right, #fff 1px, transparent 1px), linear-gradient(to bottom, #fff 1px, transparent 1px)",
          backgroundSize: "64px 64px",
        }}
      />

      <div className="relative max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Badge */}
        <div className="flex justify-center mb-4">
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-guardian-700/50 border border-guardian-500/40 text-guardian-200 text-xs font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            Beta
          </span>
        </div>

        <h2 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
          {c.heading}
        </h2>

        <p className="mt-4 text-guardian-300 text-base md:text-lg leading-relaxed">
          {c.subheading}
        </p>

        {status === "success" ? (
          <div className="mt-8 inline-flex items-center gap-2 px-6 py-4 rounded-xl bg-green-900/40 border border-green-600/50 text-green-300 text-sm font-medium">
            <span className="text-green-400">✓</span>
            {c.success}
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={c.placeholder}
              disabled={status === "loading"}
              className="flex-1 min-w-0 px-4 py-3 rounded-xl bg-guardian-900/70 border border-guardian-600/60 text-white placeholder-guardian-400 text-sm focus:outline-none focus:ring-2 focus:ring-guardian-400 focus:border-transparent disabled:opacity-50 transition"
            />
            <button
              type="submit"
              disabled={status === "loading" || !email.trim()}
              className="shrink-0 px-6 py-3 rounded-xl bg-guardian-500 hover:bg-guardian-400 active:bg-guardian-600 text-white font-semibold text-sm transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {status === "loading" ? c.buttonLoading : c.button}
            </button>
          </form>
        )}

        {status === "error" && (
          <p className="mt-3 text-red-400 text-sm">{c.error}</p>
        )}

        <p className="mt-4 text-guardian-500 text-xs">{c.disclaimer}</p>
      </div>
    </section>
  );
}
