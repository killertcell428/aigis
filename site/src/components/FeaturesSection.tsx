"use client";

import { useLanguage } from "@/contexts/LanguageContext";
import { t, tx } from "@/lib/translations";

export default function FeaturesSection() {
  const { lang } = useLanguage();

  const features = [
    { mark: "LLM01", title: tx(t.features.f1Title, lang), desc: tx(t.features.f1Desc, lang), tag: "Input · OWASP LLM01", tagColor: "bg-red-50 text-red-700 border border-red-200" },
    { mark: "LLM02", title: tx(t.features.f2Title, lang), desc: tx(t.features.f2Desc, lang), tag: "Output · OWASP LLM02", tagColor: "bg-orange-50 text-orange-700 border border-orange-200" },
    { mark: "SQL",   title: tx(t.features.f3Title, lang), desc: tx(t.features.f3Desc, lang), tag: "Input · CWE-89", tagColor: "bg-red-50 text-red-700 border border-red-200" },
    { mark: "HitL",  title: tx(t.features.f4Title, lang), desc: tx(t.features.f4Desc, lang), tag: lang === "ja" ? "コア · デフォルトSLA 30分" : "Core · 30-min default SLA", tagColor: "bg-guardian-50 text-guardian-700 border border-guardian-200" },
    { mark: "POL",   title: tx(t.features.f5Title, lang), desc: tx(t.features.f5Desc, lang), tag: lang === "ja" ? "設定" : "Configuration", tagColor: "bg-purple-50 text-purple-700 border border-purple-200" },
    { mark: "AUD",   title: tx(t.features.f6Title, lang), desc: tx(t.features.f6Desc, lang), tag: lang === "ja" ? "コンプライアンス · SOC2対応" : "Compliance · SOC2 ready", tagColor: "bg-green-50 text-green-700 border border-green-200" },
    { mark: "CAP",   title: lang === "ja" ? "Capability-Based Access Control" : "Capability-Based Access Control", desc: lang === "ja" ? "CaMeL論文に基づく制御フロー/データフロー分離。暗号ノンスCapabilityトークンで注入テキストからの偽造を防止。UNTRUSTEDデータは制御フロー操作をブロック。" : "CaMeL-inspired control/data flow separation. Cryptographic nonce Capability tokens prevent forgery from injected text. UNTRUSTED data is blocked from control-flow operations.", tag: lang === "ja" ? "Layer 4 · v1.3" : "Layer 4 · v1.3", tagColor: "bg-yellow-50 text-yellow-700 border border-yellow-200" },
    { mark: "AEP",   title: lang === "ja" ? "Atomic Execution Pipeline" : "Atomic Execution Pipeline", desc: lang === "ja" ? "ツール実行を「スキャン→実行→蒸発」の不可分操作に。ProcessSandboxで隔離実行、Vaporizerで成果物を確実に破壊。副作用を完全制御。" : "Tool execution as an indivisible Scan-Execute-Vaporize primitive. ProcessSandbox for isolated execution, Vaporizer for secure artifact destruction. Full side-effect control.", tag: lang === "ja" ? "Layer 5 · v1.3" : "Layer 5 · v1.3", tagColor: "bg-orange-50 text-orange-700 border border-orange-200" },
    { mark: "SAFE",  title: lang === "ja" ? "Safety Specification & Verifier" : "Safety Specification & Verifier", desc: lang === "ja" ? "宣言的な安全仕様(SafetySpec)を定義し、実行前に検証。合格時にProofCertificate(UUID4+タイムスタンプ)を発行。組み込み不変条件チェック付き。" : "Define declarative SafetySpecs and verify before execution. Issues ProofCertificate (UUID4 + timestamp) on pass. Built-in invariant checks for secrets, PII, and path traversal.", tag: lang === "ja" ? "Layer 6 · v1.3" : "Layer 6 · v1.3", tagColor: "bg-pink-50 text-pink-700 border border-pink-200" },
    { mark: "SLACK", title: lang === "ja" ? "Slack リアルタイム通知" : "Slack Real-time Alerts", desc: lang === "ja" ? "脅威ブロック時にBlock Kit リッチメッセージで即座に通知。テナント別に通知設定をカスタマイズ可能。" : "Instant Block Kit rich messages when threats are blocked. Per-tenant notification preferences configurable via dashboard.", tag: lang === "ja" ? "通知 · Webhook" : "Notifications · Webhook", tagColor: "bg-blue-50 text-blue-700 border border-blue-200" },
    { mark: "RPT",   title: lang === "ja" ? "コンプライアンスレポート自動生成" : "Compliance Report Auto-Generation", desc: lang === "ja" ? "OWASP LLM Top 10（100%）、SOC2、GDPR、日本AI規制37要件（AI事業者GL v1.2完全対応）をPDF・Excel・CSVで自動出力。四半期監査に即対応。" : "Auto-generate PDF/Excel/CSV reports covering OWASP LLM Top 10 (100%), SOC2, GDPR, and 37 Japan AI regulations (full v1.2 compliance). Audit-ready.", tag: lang === "ja" ? "Business · PDF/Excel" : "Business · PDF/Excel", tagColor: "bg-green-50 text-green-700 border border-green-200" },
    { mark: "PAY",   title: lang === "ja" ? "Stripe 決済 & プラン管理" : "Stripe Billing & Plan Management", desc: lang === "ja" ? "14日無料トライアル。Pro/Businessプランの自動課金、Customer Portal でセルフサービス管理。プランに応じた機能ゲート。" : "14-day free trial. Auto-billing for Pro/Business plans with Stripe Customer Portal. Feature gating based on plan tier.", tag: lang === "ja" ? "SaaS · 課金" : "SaaS · Billing", tagColor: "bg-purple-50 text-purple-700 border border-purple-200" },
  ];

  return (
    <section id="features" className="py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <p className="text-guardian-600 text-sm font-semibold uppercase tracking-widest mb-3">{tx(t.features.label, lang)}</p>
          <h2 className="section-heading">{tx(t.features.heading, lang)}</h2>
          <p className="section-subheading">{tx(t.features.sub, lang)}</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f) => (
            <div key={f.mark} className="card hover:shadow-md transition-shadow group">
              <div className="flex items-start justify-between mb-3">
                <span className="text-xs font-mono font-bold text-guardian-500 bg-guardian-50 border border-guardian-200 rounded px-2 py-0.5">
                  {f.mark}
                </span>
                <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${f.tagColor}`}>{f.tag}</span>
              </div>
              <h3 className="font-bold text-gray-900 mb-2 group-hover:text-guardian-600 transition-colors text-[15px] leading-snug">{f.title}</h3>
              <p className="text-sm text-gray-600 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>

        <p className="text-center text-xs text-gray-400 mt-10">{tx(t.features.footnote, lang)}</p>
      </div>
    </section>
  );
}
