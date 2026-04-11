"use client";

import { useLanguage } from "@/contexts/LanguageContext";
import { t, tx } from "@/lib/translations";

export default function SocialProofBar() {
  const { lang } = useLanguage();

  const STATS = [
    { value: "43+", label: tx(t.stats.rules, lang) },
    { value: "<5 ms", label: tx(t.stats.latency, lang) },
    { value: "OWASP LLM Top 10", label: tx(t.stats.owasp, lang) },
    { value: "99.9%", label: tx(t.stats.uptime, lang) },
    { value: "SOC2-ready", label: tx(t.stats.soc2, lang) },
    { value: lang === "ja" ? "AI推進法" : "JP AI Act", label: tx(t.stats.japanReady, lang) },
  ];

  return (
    <section className="bg-white border-y border-gray-100 py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-6 gap-8 text-center">
          {STATS.map((stat) => (
            <div key={stat.label}>
              <div className="text-lg font-extrabold text-guardian-600 mb-0.5">{stat.value}</div>
              <div className="text-xs text-gray-500">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
