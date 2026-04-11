"use client";

import Link from "next/link";
import clsx from "clsx";
import { useLanguage } from "@/contexts/LanguageContext";
import { t, tx } from "@/lib/translations";

export default function PricingSection() {
  const { lang } = useLanguage();
  const ja = lang === "ja";

  const FREE_PLAN = {
    name: tx(t.pricing.free.name, lang),
    price: "$0",
    period: tx(t.pricing.free.period, lang),
    tagline: tx(t.pricing.free.tagline, lang),
    features: [
      tx(t.pricing.free.f1, lang),
      tx(t.pricing.free.f2, lang),
      tx(t.pricing.free.f3, lang),
      tx(t.pricing.free.f4, lang),
      tx(t.pricing.free.f5, lang),
      tx(t.pricing.free.f6, lang),
    ],
    cta: tx(t.pricing.free.cta, lang),
    ctaHref: "https://github.com/killertcell428/aigis",
    highlight: false,
    badge: "OSS",
  };

  const PAID_PLANS = [
    {
      name: tx(t.pricing.starter.name, lang),
      price: "$49",
      period: tx(t.pricing.starter.period, lang),
      tagline: tx(t.pricing.starter.tagline, lang),
      features: [
        tx(t.pricing.starter.f1, lang),
        tx(t.pricing.starter.f2, lang),
        tx(t.pricing.starter.f3, lang),
        tx(t.pricing.starter.f4, lang),
        tx(t.pricing.starter.f5, lang),
        tx(t.pricing.starter.f6, lang),
      ],
      cta: tx(t.pricing.starter.cta, lang),
      ctaHref: "#waitlist",
      highlight: false,
      trialBadge: ja ? "14日間無料" : "14-day free trial",
    },
    {
      name: tx(t.pricing.business.name, lang),
      price: "$299",
      period: tx(t.pricing.business.period, lang),
      tagline: tx(t.pricing.business.tagline, lang),
      features: [
        tx(t.pricing.business.f1, lang),
        tx(t.pricing.business.f2, lang),
        tx(t.pricing.business.f3, lang),
        tx(t.pricing.business.f4, lang),
        tx(t.pricing.business.f5, lang),
        tx(t.pricing.business.f6, lang),
        tx(t.pricing.business.f7, lang),
      ],
      cta: tx(t.pricing.business.cta, lang),
      ctaHref: "#waitlist",
      highlight: true,
      badge: tx(t.pricing.business.badge, lang),
      trialBadge: ja ? "14日間無料" : "14-day free trial",
    },
  ];

  const ENTERPRISE = {
    name: tx(t.pricing.enterprise.name, lang),
    price: ja ? "要相談" : "Custom",
    period: tx(t.pricing.enterprise.period, lang),
    tagline: tx(t.pricing.enterprise.tagline, lang),
    features: [
      tx(t.pricing.enterprise.f1, lang),
      tx(t.pricing.enterprise.f2, lang),
      tx(t.pricing.enterprise.f3, lang),
      tx(t.pricing.enterprise.f4, lang),
      tx(t.pricing.enterprise.f5, lang),
      tx(t.pricing.enterprise.f6, lang),
    ],
    cta: tx(t.pricing.enterprise.cta, lang),
    ctaHref: "/contact",
  };

  return (
    <section id="pricing" className="py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <p className="text-guardian-600 text-sm font-semibold uppercase tracking-widest mb-3">
            {tx(t.pricing.label, lang)}
          </p>
          <h2 className="section-heading">{tx(t.pricing.heading, lang)}</h2>
          <p className="section-subheading">{tx(t.pricing.sub, lang)}</p>
        </div>

        {/* Free + Pro + Business — 3 columns */}
        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto items-start">
          {/* Free plan */}
          <div className="rounded-2xl border-2 border-guardian-200 bg-white p-8 relative">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2">
              <span className="bg-guardian-100 text-guardian-700 text-xs font-bold px-3 py-1 rounded-full border border-guardian-200">
                {FREE_PLAN.badge}
              </span>
            </div>
            <div className="mb-6">
              <h3 className="text-xl font-bold text-gray-900 mb-1">{FREE_PLAN.name}</h3>
              <p className="text-sm text-gray-500">{FREE_PLAN.tagline}</p>
            </div>
            <div className="mb-6">
              <span className="text-4xl font-extrabold text-gray-900">{FREE_PLAN.price}</span>
              <span className="text-sm ml-2 text-gray-500">{FREE_PLAN.period}</span>
            </div>
            <ul className="space-y-3 mb-8">
              {FREE_PLAN.features.map((feature) => (
                <li key={feature} className="flex items-start gap-2 text-sm">
                  <span className="text-guardian-600">✓</span>
                  <span className="text-gray-700">{feature}</span>
                </li>
              ))}
            </ul>
            <a
              href={FREE_PLAN.ctaHref}
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full text-center py-2.5 rounded-lg font-semibold text-sm transition-colors border-2 border-guardian-600 text-guardian-700 hover:bg-guardian-50"
            >
              {FREE_PLAN.cta}
            </a>
          </div>

          {/* Paid plans */}
          {PAID_PLANS.map((plan) => (
            <div
              key={plan.name}
              className={clsx(
                "rounded-2xl border p-8 relative",
                plan.highlight
                  ? "bg-guardian-600 border-guardian-500 text-white shadow-xl shadow-guardian-200 scale-105"
                  : "bg-white border-gray-200"
              )}
            >
              {plan.badge && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-guardian-400 text-white text-xs font-bold px-3 py-1 rounded-full">
                    {plan.badge}
                  </span>
                </div>
              )}

              <div className="mb-6">
                <h3 className={clsx("text-xl font-bold mb-1", plan.highlight ? "text-white" : "text-gray-900")}>
                  {plan.name}
                </h3>
                <p className={clsx("text-sm", plan.highlight ? "text-guardian-200" : "text-gray-500")}>
                  {plan.tagline}
                </p>
              </div>

              <div className="mb-6">
                <span className={clsx("text-4xl font-extrabold", plan.highlight ? "text-white" : "text-gray-900")}>
                  {plan.price}
                </span>
                <span className={clsx("text-sm ml-2", plan.highlight ? "text-guardian-200" : "text-gray-500")}>
                  {plan.period}
                </span>
                {plan.trialBadge && (
                  <div className={clsx("mt-2 inline-block text-xs font-semibold px-2.5 py-1 rounded-full",
                    plan.highlight
                      ? "bg-white/20 text-white"
                      : "bg-green-100 text-green-700"
                  )}>
                    {plan.trialBadge}
                  </div>
                )}
              </div>

              <ul className="space-y-3 mb-8">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm">
                    <span className={plan.highlight ? "text-guardian-200" : "text-guardian-600"}>✓</span>
                    <span className={plan.highlight ? "text-guardian-100" : "text-gray-700"}>{feature}</span>
                  </li>
                ))}
              </ul>

              <Link
                href={plan.ctaHref}
                className={clsx(
                  "block w-full text-center py-2.5 rounded-lg font-semibold text-sm transition-colors",
                  plan.highlight
                    ? "bg-white text-guardian-700 hover:bg-guardian-50"
                    : "btn-primary"
                )}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>

        {/* Enterprise — compact banner */}
        <div className="max-w-5xl mx-auto mt-8">
          <div className="bg-white border border-gray-200 rounded-xl px-8 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-gray-900 text-white flex items-center justify-center text-sm font-bold flex-shrink-0">
                E
              </div>
              <div>
                <h3 className="font-bold text-gray-900">{ENTERPRISE.name}</h3>
                <p className="text-sm text-gray-500">{ENTERPRISE.tagline}</p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <ul className="hidden lg:flex items-center gap-4 text-xs text-gray-500">
                {ENTERPRISE.features.slice(0, 3).map((f) => (
                  <li key={f} className="flex items-center gap-1">
                    <span className="text-guardian-600">✓</span> {f}
                  </li>
                ))}
              </ul>
              <Link
                href={ENTERPRISE.ctaHref}
                className="btn-primary text-sm px-6 py-2.5 whitespace-nowrap"
              >
                {ENTERPRISE.cta}
              </Link>
            </div>
          </div>
        </div>

        {/* 3-Layer Value Proposition */}
        <div className="mt-20 max-w-4xl mx-auto">
          <h3 className="text-2xl font-bold text-gray-900 text-center mb-3">
            {ja ? "3層の価値で、導入から定着まで" : "Three layers of value, from adoption to retention"}
          </h3>
          <p className="text-center text-gray-500 mb-10 max-w-xl mx-auto text-sm">
            {ja
              ? "OSSライブラリで入り口を開き、ダッシュボードで可視化し、コンプライアンスで定着する"
              : "Start with the OSS library, visualize with the dashboard, retain with compliance"}
          </p>
          <div className="space-y-4">
            <ValueLayer
              number="1"
              title={ja ? "OSSセキュリティライブラリ（6層防御）" : "OSS Security Library (6-Layer Defense)"}
              desc={ja
                ? "pip install aigis で即座にLLMアプリを保護。165+検出パターン（25+脅威カテゴリ）、CaMeL Capabilities（権限制御）、Atomic Execution Pipeline（実行隔離）、Safety Verifier（安全性証明）、MCPスキャナー、自動レッドチーム。永久無料でセキュリティの入り口を開く。"
                : "Protect LLM apps instantly with pip install aigis. 165+ detection patterns (25+ threat categories), CaMeL Capabilities (access control), Atomic Execution Pipeline (sandboxed execution), Safety Verifier (provable safety), MCP scanner, automated red team. Free forever to open the door to security."}
              plan="Free"
              color="bg-guardian-50 border-guardian-200"
            />
            <ValueLayer
              number="2"
              title={ja ? "クラウドダッシュボード" : "Cloud Dashboard"}
              desc={ja
                ? "チーム全体のLLMリクエストをリアルタイム可視化。リスクスコア推移、脅威ブロック統計、Playgroundでの動作テスト。チームで共有した瞬間、価値が倍増する。"
                : "Real-time visibility into all LLM requests across your team. Risk score trends, threat blocking stats, Playground testing. Value multiplies the moment you share with your team."}
              plan="Pro"
              color="bg-blue-50 border-blue-200"
            />
            <ValueLayer
              number="3"
              title={ja ? "コンプライアンス・ガバナンス" : "Compliance & Governance"}
              desc={ja
                ? "OWASP LLM Top 10、SOC2、GDPR、AI事業者ガイドラインv1.2対応のコンプライアンスレポートを自動生成。イミュータブル監査ログ、SSO統合。"
                : "Auto-generate compliance reports for OWASP LLM Top 10, SOC2, GDPR, Japan AI Guidelines v1.2. Immutable audit logs, SSO integration."}
              plan="Business"
              color="bg-purple-50 border-purple-200"
            />
          </div>
        </div>

        {/* Target Industries */}
        <div className="mt-20 max-w-4xl mx-auto text-center">
          <h3 className="text-2xl font-bold text-gray-900 mb-3">
            {ja ? "規制産業に最適化" : "Optimized for Regulated Industries"}
          </h3>
          <p className="text-gray-500 mb-8 text-sm max-w-xl mx-auto">
            {ja
              ? "情シス部門がGOを出せるセキュリティ。業界別のコンプライアンス要件に対応。"
              : "Security that IT departments can approve. Industry-specific compliance built in."}
          </p>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {[
              { icon: "🏦", label: ja ? "金融" : "Finance", sub: ja ? "SOC2 / FISC" : "SOC2 / FISC" },
              { icon: "🏥", label: ja ? "ヘルスケア" : "Healthcare", sub: ja ? "HIPAA対応" : "HIPAA ready" },
              { icon: "🏛️", label: ja ? "政府・自治体" : "Government", sub: ja ? "ISMAP準拠" : "ISMAP aligned" },
              { icon: "🏭", label: ja ? "製造業" : "Manufacturing", sub: ja ? "IP保護" : "IP protection" },
              { icon: "⚖️", label: ja ? "法律" : "Legal", sub: ja ? "守秘義務対応" : "Confidentiality" },
            ].map((industry) => (
              <div key={industry.label} className="bg-white border border-gray-200 rounded-xl p-4 hover:shadow-md transition-shadow">
                <div className="text-2xl mb-2">{industry.icon}</div>
                <div className="font-semibold text-gray-900 text-sm">{industry.label}</div>
                <div className="text-xs text-gray-500 mt-0.5">{industry.sub}</div>
              </div>
            ))}
          </div>
        </div>

        <p className="text-center text-sm text-gray-400 mt-10">
          {tx(t.pricing.footnote, lang)}
        </p>
      </div>
    </section>
  );
}

function ValueLayer({
  number,
  title,
  desc,
  plan,
  color,
}: {
  number: string;
  title: string;
  desc: string;
  plan: string;
  color: string;
}) {
  return (
    <div className={`border rounded-xl p-6 ${color} flex gap-5 items-start`}>
      <div className="w-10 h-10 rounded-full bg-guardian-600 text-white flex items-center justify-center text-sm font-bold flex-shrink-0">
        {number}
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-3 mb-1">
          <h4 className="font-bold text-gray-900">{title}</h4>
          <span className="text-xs px-2 py-0.5 rounded-full bg-white border border-gray-300 text-gray-600 font-medium">
            {plan}+
          </span>
        </div>
        <p className="text-sm text-gray-600 leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}
