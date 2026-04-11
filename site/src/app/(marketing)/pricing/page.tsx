"use client";

import PricingSection from "@/components/PricingSection";
import { useLanguage } from "@/contexts/LanguageContext";

const COMPARISON_ROWS_EN = [
  { feature: "Team members", values: ["1 (personal)", "Up to 5", "Up to 50", "Unlimited"] },
  { feature: "API requests / month", values: ["Unlimited (CLI)", "500K", "5M", "Unlimited"] },
  { feature: "Detection patterns (165+), 6-layer defense", values: [true, true, true, true] },
  { feature: "MCP Security Scanner", values: [true, true, true, true] },
  { feature: "Red Team testing (CLI)", values: [true, true, true, true] },
  { feature: "Cloud dashboard", values: [false, true, true, true] },
  { feature: "Risk score visualization", values: [false, true, true, true] },
  { feature: "Playground (prompt testing)", values: [false, true, true, true] },
  { feature: "Custom detection rules", values: ["CLI only", "Unlimited", "Unlimited", "Unlimited"] },
  { feature: "Human-in-the-Loop review", values: [false, false, true, true] },
  { feature: "Data retention", values: ["—", "90 days", "1 year", "Unlimited"] },
  { feature: "Compliance reports (OWASP, SOC2)", values: [false, false, true, true] },
  { feature: "SSO / SAML", values: [false, false, true, true] },
  { feature: "Slack / PagerDuty alerts", values: [false, false, true, true] },
  { feature: "On-premises / VPC", values: [false, false, false, true] },
  { feature: "SLA guarantee", values: ["—", "99.5%", "99.9%", "99.99%"] },
  { feature: "Support", values: ["GitHub Issues", "Email", "Priority (Chat + Email)", "Dedicated CSM"] },
];

const COMPARISON_ROWS_JA = [
  { feature: "チームメンバー", values: ["1名（個人）", "最大5名", "最大50名", "無制限"] },
  { feature: "月間APIリクエスト", values: ["無制限（CLI）", "50万", "500万", "無制限"] },
  { feature: "検出パターン（165+種）、6層防御", values: [true, true, true, true] },
  { feature: "MCPセキュリティスキャナー", values: [true, true, true, true] },
  { feature: "レッドチームテスト（CLI）", values: [true, true, true, true] },
  { feature: "クラウドダッシュボード", values: [false, true, true, true] },
  { feature: "リスクスコア可視化", values: [false, true, true, true] },
  { feature: "Playground（プロンプトテスト）", values: [false, true, true, true] },
  { feature: "カスタム検出ルール", values: ["CLIのみ", "無制限", "無制限", "無制限"] },
  { feature: "Human-in-the-Loopレビュー", values: [false, false, true, true] },
  { feature: "データ保持期間", values: ["—", "90日", "1年", "無制限"] },
  { feature: "コンプラレポート（OWASP, SOC2）", values: [false, false, true, true] },
  { feature: "SSO / SAML", values: [false, false, true, true] },
  { feature: "Slack / PagerDuty通知", values: [false, false, true, true] },
  { feature: "オンプレミス / VPC", values: [false, false, false, true] },
  { feature: "SLA保証", values: ["—", "99.5%", "99.9%", "99.99%"] },
  { feature: "サポート", values: ["GitHub Issues", "メール", "優先（チャット + メール）", "専任CSM"] },
];

const PLAN_NAMES = ["Free", "Pro", "Business", "Enterprise"];
const PLAN_PRICES_EN = ["$0", "$49/mo", "$299/mo", "Custom"];
const PLAN_PRICES_JA = ["無料", "$49/月", "$299/月", "要相談"];

export default function PricingPage() {
  const { lang } = useLanguage();
  const ja = lang === "ja";
  const rows = ja ? COMPARISON_ROWS_JA : COMPARISON_ROWS_EN;
  const planPrices = ja ? PLAN_PRICES_JA : PLAN_PRICES_EN;

  return (
    <>
      {/* Page header */}
      <div className="bg-gray-950 text-white py-16 text-center">
        <h1 className="text-4xl font-extrabold tracking-tight mb-3">
          {ja ? "料金プラン" : "Pricing"}
        </h1>
        <p className="text-gray-400 text-lg max-w-xl mx-auto">
          {ja
            ? "OSSコアは永久無料。ビジネスの成長に合わせてスケール。年間契約で20%OFF。"
            : "OSS Core is free forever. Scale as your business grows. Save 20% with annual billing."}
        </p>
      </div>

      <PricingSection />

      {/* Comparison table */}
      <section className="py-16 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
            {ja ? "プラン別機能比較" : "Full Feature Comparison"}
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b-2 border-gray-200">
                  <th className="text-left py-3 px-4 text-gray-500 font-medium">
                    {ja ? "機能" : "Feature"}
                  </th>
                  {PLAN_NAMES.map((name, i) => (
                    <th key={name} className="text-center py-3 px-4">
                      <div className={`font-bold ${i === 0 ? "text-guardian-700" : "text-gray-900"}`}>
                        {name}
                        {i === 0 && <span className="ml-1 text-xs font-normal text-guardian-600">(OSS)</span>}
                      </div>
                      <div className="text-xs text-gray-500 font-normal mt-0.5">{planPrices[i]}</div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.feature} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 text-gray-700">{row.feature}</td>
                    {row.values.map((val, i) => (
                      <td key={i} className="py-3 px-4 text-center text-gray-600">
                        {val === true ? <span className="text-green-600 font-bold">✓</span>
                          : val === false ? <span className="text-gray-300">—</span>
                          : val}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Enterprise CTA */}
      <section className="py-16 bg-gray-50 text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-3">
          {ja ? "規制産業向けのカスタムプラン" : "Custom plans for regulated industries"}
        </h2>
        <p className="text-gray-500 mb-6 max-w-lg mx-auto">
          {ja
            ? "金融・ヘルスケア・政府向けのオンプレミス対応、コンプライアンス要件、カスタム契約に対応します。"
            : "On-premises deployment, compliance requirements, and custom contracts for finance, healthcare, and government."}
        </p>
        <a href="/contact" className="btn-primary px-8 py-3">
          {ja ? "営業チームに問い合わせる" : "Contact Sales"}
        </a>
      </section>
    </>
  );
}
