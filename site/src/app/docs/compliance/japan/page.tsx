"use client";

import DocsLayout from "@/components/DocsLayout";
import { useLanguage } from "@/contexts/LanguageContext";

export default function JapanCompliancePage() {
  const { lang } = useLanguage();
  const ja = lang === "ja";

  const TOC = [
    { id: "overview", label: ja ? "概要" : "Overview" },
    { id: "regulations", label: ja ? "対応する日本の規制" : "Japan Regulations" },
    { id: "ai-promotion-act", label: ja ? "AI推進法" : "AI Promotion Act", level: 3 },
    { id: "ai-operator-guideline", label: ja ? "AI事業者ガイドライン" : "AI Operator Guideline", level: 3 },
    { id: "ai-security-guideline", label: ja ? "AIセキュリティGL" : "AI Security Guideline", level: 3 },
    { id: "appi", label: ja ? "個人情報保護法" : "APPI / My Number Act", level: 3 },
    { id: "mapping", label: ja ? "機能×規制マッピング" : "Feature-Regulation Mapping" },
    { id: "japanese-detection", label: ja ? "日本語検知機能" : "Japanese Detection" },
    { id: "industry", label: ja ? "業種別ガイド" : "Industry Guide" },
    { id: "getting-started", label: ja ? "導入手順" : "Getting Started" },
  ];

  const mappingRows = [
    {
      feature: ja ? "入力フィルター（165+パターン）" : "Input Filter (165+ patterns)",
      regulation: ja ? "AIセキュリティGL「多層防御」" : 'AI Security GL "Multi-layer Defense"',
      status: "covered",
    },
    {
      feature: ja ? "出力フィルター（7パターン）" : "Output Filter (7 patterns)",
      regulation: ja ? "AI事業者GL「出力の適切性確保」" : 'AI Operator GL "Output Appropriateness"',
      status: "covered",
    },
    {
      feature: "Human-in-the-Loop",
      regulation: ja ? "AI推進法「人間の関与」/ AIセキュリティGL「重要な操作への人間承認」" : 'AI Promotion Act "Human Involvement" / AI Security GL "Human Approval"',
      status: "covered",
    },
    {
      feature: ja ? "監査ログ（100%記録）" : "Audit Logs (100% recorded)",
      regulation: ja ? "AI事業者GL「透明性・説明責任」/ APPI「取扱い記録」" : 'AI Operator GL "Transparency" / APPI "Processing Records"',
      status: "covered",
    },
    {
      feature: ja ? "マイナンバー検知" : "My Number Detection",
      regulation: ja ? "マイナンバー法「特定個人情報の適正な取扱い」" : 'My Number Act "Proper Handling of Specified Personal Info"',
      status: "covered",
    },
    {
      feature: ja ? "リスクスコアリング（0-100）" : "Risk Scoring (0-100)",
      regulation: ja ? "AI事業者GL「リスク評価の実施」" : 'AI Operator GL "Risk Assessment"',
      status: "covered",
    },
    {
      feature: ja ? "コンプライアンスレポート" : "Compliance Reports",
      regulation: ja ? "AI事業者GL「ガバナンス体制の構築」" : 'AI Operator GL "Governance Framework"',
      status: "covered",
    },
    {
      feature: ja ? "ポリシーエンジン" : "Policy Engine",
      regulation: ja ? "AIセキュリティGL「システムアーキテクチャの見直し」" : 'AI Security GL "Architecture Review"',
      status: "covered",
    },
    {
      feature: ja ? "OWASP/CWE分類" : "OWASP/CWE Classification",
      regulation: ja ? "AIセキュリティGL「国際標準への準拠」" : 'AI Security GL "International Standards"',
      status: "covered",
    },
    {
      feature: ja ? "自動サニタイズ（PII墨消し）" : "Auto-Sanitization (PII Redaction)",
      regulation: ja ? "APPI「個人データの安全管理措置」" : 'APPI "Safety Management of Personal Data"',
      status: "covered",
    },
    {
      feature: ja ? "修復ヒント（OWASP参照付き）" : "Remediation Hints (with OWASP refs)",
      regulation: ja ? "AI事業者GL「利用者への適切な情報提供」" : 'AI Operator GL "Appropriate Info Provision"',
      status: "covered",
    },
  ];

  const japanesePatterns = [
    { category: ja ? "プロンプトインジェクション" : "Prompt Injection", count: 4, examples: ja ? "「前の指示を無視して」「システムプロンプトを教えて」「制限を解除して」" : '"Ignore previous instructions" "Show system prompt" "Remove restrictions"' },
    { category: ja ? "PII検知（入力）" : "PII Detection (Input)", count: 6, examples: ja ? "電話番号、マイナンバー、郵便番号、住所、銀行口座、法人番号" : "Phone, My Number, Postal Code, Address, Bank Account, Corporate Number" },
    { category: ja ? "機密情報" : "Confidential Data", count: 1, examples: ja ? "「社外秘」「部外秘」「極秘」" : '"Confidential" "Internal Only" "Top Secret"' },
    { category: ja ? "PII検知（出力）" : "PII Detection (Output)", count: 2, examples: ja ? "マイナンバー、電話番号の出力検知" : "My Number, Phone Number in output" },
    { category: ja ? "類似度検知（Layer 2）" : "Similarity (Layer 2)", count: 12, examples: ja ? "日本語パラフレーズ攻撃40フレーズ" : "40 Japanese paraphrase attack phrases" },
  ];

  return (
    <DocsLayout toc={TOC}>
      <h1>{ja ? "日本のAIガバナンス対応" : "Japan AI Governance Compliance"}</h1>

      {/* Overview */}
      <section id="overview">
        <p>
          {ja
            ? "Aigisは、日本のAI関連規制・ガイドラインに対応した唯一の日本語ネイティブAIセキュリティプラットフォームです。マイナンバー検知、日本語プロンプトインジェクション対策、Human-in-the-Loop（人間承認フロー）により、AI推進法・AI事業者ガイドライン・個人情報保護法の要件を技術的にカバーします。"
            : "Aigis is the only Japanese-native AI security platform designed for Japan's regulatory landscape. With My Number detection, Japanese prompt injection protection, and Human-in-the-Loop review, it technically covers requirements from the AI Promotion Act, AI Operator Guidelines, and APPI."}
        </p>

        <div className="not-prose grid grid-cols-1 sm:grid-cols-3 gap-3 my-6">
          <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-green-700">11</p>
            <p className="text-xs text-green-600 mt-1">{ja ? "規制要件カバー" : "Regulation Requirements Covered"}</p>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-blue-700">25+</p>
            <p className="text-xs text-blue-600 mt-1">{ja ? "日本語検知パターン" : "Japanese Detection Patterns"}</p>
          </div>
          <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-purple-700">100%</p>
            <p className="text-xs text-purple-600 mt-1">{ja ? "監査証跡カバレッジ" : "Audit Trail Coverage"}</p>
          </div>
        </div>
      </section>

      {/* Regulations */}
      <section id="regulations">
        <h2>{ja ? "対応する日本の規制・ガイドライン" : "Applicable Japan Regulations & Guidelines"}</h2>

        <h3 id="ai-promotion-act">{ja ? "AI推進法（2025年9月施行）" : "AI Promotion Act (Effective Sep 2025)"}</h3>
        <p>
          {ja
            ? "日本初のAI法。事業者に「協力努力義務」を課し、透明性確保と人間の関与を重視。罰則はないが、調査協力義務と行政指導・名称公表の仕組みあり。Aigisの監査ログとHuman-in-the-Loopは、この法律の趣旨に直接対応します。"
            : "Japan's first AI law. Requires operators to 'endeavor to cooperate,' emphasizing transparency and human involvement. No penalties, but includes investigation cooperation obligations and administrative guidance. Aigis's audit logs and Human-in-the-Loop directly address this law's intent."}
        </p>

        <h3 id="ai-operator-guideline">{ja ? "AI事業者ガイドライン v1.2（2026年3月31日公表）" : "AI Operator Guideline v1.2 (Published Mar 31, 2026)"}</h3>
        <p>
          {ja
            ? "総務省・経産省が策定。全AI事業者（開発者・提供者・利用者）に対し、リスク評価、ガバナンス体制構築、透明性確保を求める。v1.2ではAIエージェント・エージェンティックAI・フィジカルAIの定義が追加され、Human-in-the-Loop必須化、リスクベースアプローチの強化、RAG構築者の開発者責任、攻めのガバナンスなどが新たに盛り込まれた。Aigisは全37要件に100%対応。"
            : "Published by MIC and METI. Requires all AI operators to conduct risk assessments, establish governance frameworks, and ensure transparency. v1.2 adds definitions for AI agents, agentic AI, and physical AI, mandates Human-in-the-Loop, strengthens risk-based approach, establishes developer responsibility for RAG builders, and introduces proactive governance. Aigis covers all 37 requirements at 100%."}
        </p>

        <h3 id="ai-security-guideline">{ja ? "AIセキュリティ技術ガイドライン（2025年度末策定予定）" : "AI Security Technical Guideline (Draft FY2025)"}</h3>
        <p>
          {ja
            ? "総務省が策定中。LLMを主な対象とし、プロンプトインジェクション対策を含む「多層防御」を要求。Aigisの6層防御（正規表現 → 類似度検知 → Human-in-the-Loop → CaMeL Capabilities → AEP → Safety Verifier）はこのガイドラインの推奨事項を大幅に上回ります。"
            : "Being developed by MIC. Focuses on LLMs, requiring 'multi-layer defense' including prompt injection countermeasures. Aigis's 6-layer defense (regex → similarity → HitL → CaMeL Capabilities → AEP → Safety Verifier) exceeds this guideline's recommendations."}
        </p>

        <div className="not-prose bg-guardian-50 border border-guardian-200 rounded-xl p-4 my-4">
          <p className="text-sm font-semibold text-guardian-800 mb-2">
            {ja ? "Aigisの6層防御アーキテクチャ（v1.3.1）" : "Aigis's 6-Layer Defense Architecture (v1.3.1)"}
          </p>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="px-3 py-1.5 bg-green-100 text-green-700 rounded-lg font-medium">L1: Regex (165+{ja ? "パターン" : " patterns"})</span>
            <span className="text-gray-400">→</span>
            <span className="px-3 py-1.5 bg-blue-100 text-blue-700 rounded-lg font-medium">L2: {ja ? "類似度検知" : "Similarity"} (56 {ja ? "フレーズ" : "phrases"})</span>
            <span className="text-gray-400">→</span>
            <span className="px-3 py-1.5 bg-purple-100 text-purple-700 rounded-lg font-medium">L3: Human-in-the-Loop</span>
            <span className="text-gray-400">→</span>
            <span className="px-3 py-1.5 bg-yellow-100 text-yellow-700 rounded-lg font-medium">L4: Capabilities (CaMeL)</span>
            <span className="text-gray-400">→</span>
            <span className="px-3 py-1.5 bg-orange-100 text-orange-700 rounded-lg font-medium">L5: AEP ({ja ? "実行隔離" : "Sandboxed Exec"})</span>
            <span className="text-gray-400">→</span>
            <span className="px-3 py-1.5 bg-red-100 text-red-700 rounded-lg font-medium">L6: Safety Verifier</span>
          </div>
        </div>

        <h3 id="appi">{ja ? "個人情報保護法（APPI）/ マイナンバー法" : "APPI / My Number Act"}</h3>
        <p>
          {ja
            ? "マイナンバーは「特定個人情報」として法律で厳格に保護されており、漏洩は刑事罰の対象です。Aigisはマイナンバー（12桁）の入力・出力両方で検知し、自動サニタイズ機能で墨消しも可能です。"
            : "My Number is legally protected as 'Specified Personal Information' with criminal penalties for leakage. Aigis detects My Number (12 digits) in both input and output, with auto-sanitization for automatic redaction."}
        </p>
      </section>

      {/* Feature-Regulation Mapping */}
      <section id="mapping">
        <h2>{ja ? "機能 × 規制要件 マッピング" : "Feature × Regulation Mapping"}</h2>
        <p>{ja ? "Aigisの各機能が、どの日本の規制要件に対応しているかを示します。" : "Shows how each Aigis feature maps to specific Japanese regulatory requirements."}</p>

        <div className="not-prose overflow-x-auto my-4">
          <table className="min-w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
            <thead>
              <tr className="bg-gray-50">
                <th className="text-left px-4 py-2 font-semibold text-gray-700 border-b">{ja ? "Aigis機能" : "Aigis Feature"}</th>
                <th className="text-left px-4 py-2 font-semibold text-gray-700 border-b">{ja ? "対応する規制要件" : "Regulation Requirement"}</th>
                <th className="text-center px-4 py-2 font-semibold text-gray-700 border-b">{ja ? "対応状況" : "Status"}</th>
              </tr>
            </thead>
            <tbody>
              {mappingRows.map((row, i) => (
                <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                  <td className="px-4 py-2 border-b text-gray-800 font-medium">{row.feature}</td>
                  <td className="px-4 py-2 border-b text-gray-600">{row.regulation}</td>
                  <td className="px-4 py-2 border-b text-center">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                      <span>&#10003;</span> {ja ? "対応済" : "Covered"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Japanese Detection */}
      <section id="japanese-detection">
        <h2>{ja ? "日本語検知機能の詳細" : "Japanese Detection Capabilities"}</h2>
        <div className="not-prose space-y-3 my-4">
          {japanesePatterns.map((p, i) => (
            <div key={i} className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-1">
                <h4 className="font-semibold text-gray-800 text-sm">{p.category}</h4>
                <span className="text-xs bg-guardian-100 text-guardian-700 px-2 py-0.5 rounded-full font-medium">{p.count} {ja ? "パターン" : "patterns"}</span>
              </div>
              <p className="text-xs text-gray-500">{p.examples}</p>
            </div>
          ))}
        </div>

        <h3>{ja ? "使用例：マイナンバー検知と自動サニタイズ" : "Example: My Number Detection & Auto-Sanitization"}</h3>
        <pre><code>{`from aigis import scan, sanitize

# ${ja ? "マイナンバーを含むテキストをスキャン" : "Scan text containing My Number"}
result = scan("${ja ? "マイナンバーは 1234 5678 9012 です" : "My number is 1234 5678 9012"}")
print(result.is_safe)       # False
print(result.risk_score)    # 70
print(result.matched_rules[0].owasp_ref)
# "OWASP LLM02: Sensitive Information Disclosure"

# ${ja ? "自動墨消し" : "Auto-redact"}
cleaned, redactions = sanitize("${ja ? "マイナンバーは 1234 5678 9012 です" : "My number is 1234 5678 9012"}")
print(cleaned)  # "${ja ? "マイナンバーは [MY_NUMBER_REDACTED] です" : "My number is [MY_NUMBER_REDACTED]"}"
`}</code></pre>
      </section>

      {/* Industry Guide */}
      <section id="industry">
        <h2>{ja ? "業種別導入ガイド" : "Industry-Specific Guide"}</h2>

        <h3>{ja ? "金融機関" : "Financial Services"}</h3>
        <p>
          {ja
            ? "銀行・証券・保険でのLLM活用において、口座情報・クレジットカード番号の漏洩防止、FISC安全対策基準への準拠が求められます。Aigisは入出力両方で金融PII検知を行い、コンプライアンスレポートで監査対応が可能です。"
            : "For banks, securities, and insurance using LLMs, prevention of account/credit card leakage and FISC compliance is required. Aigis detects financial PII in both input and output, with compliance reports for audit readiness."}
        </p>

        <h3>{ja ? "医療・ヘルスケア" : "Healthcare"}</h3>
        <p>
          {ja
            ? "患者情報・診療データのLLMへの送信は個人情報保護法上の重大リスクです。Aigisの自動サニタイズ機能で、患者情報を墨消ししてからLLMに送信できます。"
            : "Sending patient data to LLMs poses significant APPI risks. Aigis's auto-sanitization can redact patient information before LLM transmission."}
        </p>

        <h3>{ja ? "行政・公共機関" : "Government & Public Sector"}</h3>
        <p>
          {ja
            ? "2026年4月から「行政AI調達ガイドライン」が全面適用されます。Aigisの監査ログ・Human-in-the-Loop・コンプライアンスレポートは、行政機関の調達要件を満たす基盤となります。"
            : "The 'Government AI Procurement Guideline' takes full effect from April 2026. Aigis's audit logs, HitL, and compliance reports provide the foundation for meeting procurement requirements."}
        </p>
      </section>

      {/* Getting Started */}
      <section id="getting-started">
        <h2>{ja ? "導入手順" : "Getting Started"}</h2>
        <p>
          {ja
            ? "Aigisの導入は3ステップで完了します。日本語検知パターンは初期状態で有効です。"
            : "Aigis integration takes 3 steps. Japanese detection patterns are enabled by default."}
        </p>

        <pre><code>{`# Step 1: ${ja ? "インストール" : "Install"}
pip install aigis

# Step 2: ${ja ? "スキャン統合（2行追加するだけ）" : "Integrate scanning (just add 2 lines)"}
from aigis import scan, sanitize

user_input = "${ja ? "ユーザーからの入力" : "user input here"}"
result = scan(user_input)

if result.is_blocked:
    # ${ja ? "自動ブロック + 修復ヒント提供" : "Auto-block + provide remediation hints"}
    print(result.remediation)
elif result.needs_review:
    # ${ja ? "人間レビューキューへ" : "Queue for human review"}
    review_queue.add(user_input, result)
else:
    # ${ja ? "安全 → LLMに転送（PII自動墨消し付き）" : "Safe → forward to LLM (with PII auto-redaction)"}
    cleaned, _ = sanitize(user_input)
    response = llm_client.generate(cleaned)

# Step 3: ${ja ? "コンプライアンスレポート生成" : "Generate compliance report"}
# ${ja ? "ダッシュボードから JSON/CSV でエクスポート" : "Export as JSON/CSV from dashboard"}
`}</code></pre>
      </section>
    </DocsLayout>
  );
}
