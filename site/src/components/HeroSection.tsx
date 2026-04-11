"use client";

import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";
import { t, tx } from "@/lib/translations";

export default function HeroSection() {
  const { lang } = useLanguage();

  return (
    <section className="relative bg-gradient-to-b from-guardian-950 via-guardian-900 to-guardian-800 text-white overflow-hidden">
      <div className="absolute inset-0 opacity-10" style={{
        backgroundImage: "linear-gradient(to right, #fff 1px, transparent 1px), linear-gradient(to bottom, #fff 1px, transparent 1px)",
        backgroundSize: "64px 64px",
      }} />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-32">
        <div className="flex justify-center mb-6">
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-guardian-700/50 border border-guardian-500/40 text-guardian-200 text-xs font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            {tx(t.hero.badge, lang)}
          </span>
        </div>

        <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-center tracking-tight max-w-4xl mx-auto leading-tight">
          {tx(t.hero.headline1, lang)}{" "}
          <span className="text-guardian-300">{tx(t.hero.headline2, lang)}</span>{" "}
          {tx(t.hero.headline3, lang)}
        </h1>

        <p className="mt-6 text-lg md:text-xl text-guardian-200 text-center max-w-2xl mx-auto leading-relaxed">
          {tx(t.hero.subhead, lang)}
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center mt-10">
          <Link href="/docs/quickstart" className="btn-primary px-7 py-3 text-base">
            {tx(t.hero.ctaPrimary, lang)}
          </Link>
          <Link href="#how-it-works" className="btn-outline-white px-7 py-3 text-base">
            {tx(t.hero.ctaSecondary, lang)}
          </Link>
        </div>

        <div className="flex flex-wrap justify-center gap-x-8 gap-y-3 mt-12 text-guardian-300 text-sm">
          {[
            { mark: "⊙", key: t.hero.badge1 },
            { mark: "◈", key: t.hero.badge2 },
            { mark: "◉", key: t.hero.badge3 },
            { mark: "⚡", key: t.hero.badge4 },
          ].map((badge) => (
            <div key={badge.key.en} className="flex items-center gap-2">
              <span className="text-guardian-400 text-xs">{badge.mark}</span>
              <span>{tx(badge.key, lang)}</span>
            </div>
          ))}
        </div>

        <div className="mt-16 max-w-3xl mx-auto">
          <FlowDiagram lang={lang} />
        </div>
      </div>
    </section>
  );
}

function FlowDiagram({ lang }: { lang: "en" | "ja" }) {
  return (
    <div className="bg-guardian-900/60 border border-guardian-700/50 rounded-2xl p-8 backdrop-blur">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-sm">
        <FlowBox title={tx(t.hero.flowApp, lang)} subtitle={tx(t.hero.flowAppSub, lang)} color="border-gray-600 bg-gray-800/80" icon="⬡" />
        <Arrow label={tx(t.hero.flowAllRequests, lang)} />
        <FlowBox title={tx(t.hero.flowGuardian, lang)} subtitle={tx(t.hero.flowGuardianSub, lang)} color="border-guardian-500 bg-guardian-700/80 ring-2 ring-guardian-400/30" icon="◈" highlight />
        <Arrow label={tx(t.hero.flowSafeOnly, lang)} />
        <FlowBox title={tx(t.hero.flowLLM, lang)} subtitle={tx(t.hero.flowLLMSub, lang)} color="border-gray-600 bg-gray-800/80" icon="◉" />
      </div>

      <div className="mt-6 grid grid-cols-3 gap-4 text-xs text-center">
        <div />
        <div className="flex flex-col gap-2">
          <div className="text-guardian-400 font-medium tracking-wide uppercase text-[10px]">{tx(t.hero.routingLabel, lang)}</div>
          <div className="flex justify-center gap-3">
            <StatusPill color="green" label={tx(t.hero.routePass, lang)} />
            <StatusPill color="yellow" label={tx(t.hero.routeReview, lang)} />
            <StatusPill color="red" label={tx(t.hero.routeBlock, lang)} />
          </div>
        </div>
        <div />
      </div>
    </div>
  );
}

function FlowBox({ title, subtitle, color, icon, highlight }: { title: string; subtitle: string; color: string; icon: string; highlight?: boolean }) {
  return (
    <div className={`flex-1 min-w-[120px] border rounded-xl p-4 text-center ${color}`}>
      <div className="text-2xl mb-1 font-mono text-guardian-300">{icon}</div>
      <div className={`font-semibold ${highlight ? "text-white" : "text-gray-200"}`}>{title}</div>
      <div className="text-gray-400 text-xs mt-0.5">{subtitle}</div>
    </div>
  );
}

function Arrow({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center gap-1 text-guardian-400">
      <div className="text-xs text-guardian-300">{label}</div>
      <div className="text-lg">→</div>
    </div>
  );
}

function StatusPill({ color, label }: { color: "green" | "yellow" | "red"; label: string }) {
  const colors = {
    green: "bg-green-900/50 text-green-300 border-green-700",
    yellow: "bg-yellow-900/50 text-yellow-300 border-yellow-700",
    red: "bg-red-900/50 text-red-300 border-red-700",
  };
  return <span className={`px-2 py-0.5 rounded-full border text-xs ${colors[color]}`}>{label}</span>;
}
