"use client";

import { useLanguage } from "@/contexts/LanguageContext";

export default function RiskScoringSection() {
  const { lang } = useLanguage();
  const ja = lang === "ja";

  const RISK_LEVELS = [
    {
      level: "Low",
      range: "0 – 30",
      color: "bg-green-500",
      textColor: "text-green-700",
      bgColor: "bg-green-50 border-green-200",
      action: ja ? "自動許可" : "Auto-Allow",
      actionIcon: "✅",
      description: ja
        ? "リクエストは即座にLLMへ転送されます。遅延なし。"
        : "Request passes through immediately to the LLM. No delay.",
      examples: ja
        ? ["通常の質問", "コード補完", "データ要約"]
        : ["Normal questions", "Code completion", "Data summarization"],
    },
    {
      level: "Medium",
      range: "31 – 60",
      color: "bg-yellow-400",
      textColor: "text-yellow-700",
      bgColor: "bg-yellow-50 border-yellow-200",
      action: ja ? "レビュー待ち" : "Queue for Review",
      actionIcon: "⏳",
      description: ja
        ? "リクエストは保留されます。設定したSLA（デフォルト30分）以内に担当者がレビューします。"
        : "Request is held. A human reviewer sees it within your configured SLA (default: 30 min).",
      examples: ja
        ? ["曖昧な指示", "部分的なインジェクションパターン", "グレーゾーンのコンテンツ"]
        : ["Ambiguous instructions", "Partial injection patterns", "Borderline content"],
    },
    {
      level: "High",
      range: "61 – 80",
      color: "bg-orange-500",
      textColor: "text-orange-700",
      bgColor: "bg-orange-50 border-orange-200",
      action: ja ? "優先レビュー" : "Queue for Review",
      actionIcon: "⏳",
      description: ja
        ? "優先キュー。担当者に即座に通知が届きます。SLAタイマーが開始します。"
        : "Priority queue. Reviewers are notified immediately. SLA timer starts.",
      examples: ja
        ? ["強いインジェクションシグナル", "複数パターンのマッチ", "既知の攻撃フラグメント"]
        : ["Strong injection signals", "Multiple matched patterns", "Known attack fragments"],
    },
    {
      level: "Critical",
      range: "81 – 100",
      color: "bg-red-600",
      textColor: "text-red-700",
      bgColor: "bg-red-50 border-red-200",
      action: ja ? "自動ブロック" : "Auto-Block",
      actionIcon: "🚫",
      description: ja
        ? "リクエストは即座に拒否されます。人間レビューは不要。呼び出し元に403を返します。"
        : "Request is rejected instantly. No human review needed. 403 returned to caller.",
      examples: ja
        ? ["UNION SELECT攻撃", "DROP TABLE", "DANジェイルブレイク", "認証情報の流出"]
        : ["UNION SELECT attacks", "DROP TABLE", "DAN jailbreaks", "Credential exfiltration"],
    },
  ];

  return (
    <section id="risk-scoring" className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="section-heading">
            {ja ? "リスクスコアリングエンジン" : "Risk Scoring Engine"}
          </h2>
          <p className="section-subheading">
            {ja
              ? "すべてのリクエストに0〜100のスコアを付与。スコアに基づいてルーティングが自動で決まります。"
              : "Every request gets a score from 0 to 100. The score determines the routing action — automatically."}
          </p>
        </div>

        {/* Score bar */}
        <div className="max-w-3xl mx-auto mb-12">
          <div className="h-6 rounded-full overflow-hidden flex shadow-inner">
            <div className="bg-green-500 flex-[30] flex items-center justify-center text-white text-xs font-bold">Low</div>
            <div className="bg-yellow-400 flex-[30] flex items-center justify-center text-white text-xs font-bold">Med</div>
            <div className="bg-orange-500 flex-[20] flex items-center justify-center text-white text-xs font-bold">High</div>
            <div className="bg-red-600 flex-[20] flex items-center justify-center text-white text-xs font-bold">Critical</div>
          </div>
          <div className="flex justify-between text-xs text-gray-400 mt-1.5 px-1">
            <span>0</span>
            <span>30</span>
            <span>60</span>
            <span>80</span>
            <span>100</span>
          </div>
        </div>

        {/* Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          {RISK_LEVELS.map((level) => (
            <div key={level.level} className={`border rounded-xl p-5 ${level.bgColor}`}>
              <div className="flex items-center justify-between mb-3">
                <span className={`text-lg font-bold ${level.textColor}`}>{level.level}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-mono font-semibold ${level.textColor} bg-white/60`}>
                  {level.range}
                </span>
              </div>
              <div className={`h-1.5 rounded-full ${level.color} mb-4`} />
              <div className="flex items-center gap-1.5 mb-3">
                <span>{level.actionIcon}</span>
                <span className={`text-sm font-semibold ${level.textColor}`}>{level.action}</span>
              </div>
              <p className="text-xs text-gray-600 leading-relaxed mb-3">{level.description}</p>
              <ul className="space-y-1">
                {level.examples.map((ex) => (
                  <li key={ex} className="text-xs text-gray-500 flex items-center gap-1">
                    <span className="w-1 h-1 rounded-full bg-gray-400 flex-shrink-0" />
                    {ex}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <p className="text-center text-sm text-gray-400 mt-8">
          {ja
            ? "すべての閾値はポリシーエンジンでテナントごとに設定できます。"
            : "All thresholds are configurable per tenant via the Policy Engine."}
        </p>
      </div>
    </section>
  );
}
