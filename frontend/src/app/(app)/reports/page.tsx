"use client";

import { useEffect, useState } from "react";
import { getLang, saveLang } from "@/lib/lang";
import LangToggle from "@/components/LangToggle";
import { reportsApi, type WeeklyReport } from "@/lib/api";

const BASE = "/api/v1";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("aigis_token");
}

interface ReportData {
  report_metadata: {
    generated_at: string;
    date_from: string;
    date_to: string;
  };
  executive_summary: {
    total_requests: number;
    allowed: number;
    blocked: number;
    queued_for_review: number;
    safety_rate: number;
    block_rate: number;
    average_risk_score: number;
  };
  risk_distribution: Record<string, number>;
  compliance_summary: {
    owasp_llm_top_10: Array<{ id: string; name: string; status: string; detail: string }>;
    owasp_coverage_rate: string;
    owasp_coverage: string[];
    cwe_coverage: Array<{ id: string; name: string; patterns: number } | string>;
    human_review_rate: number;
    audit_trail: string;
  };
  soc2_compliance?: Array<{ id: string; category: string; name: string; status: string; detail: string }>;
  gdpr_compliance?: Array<{ article: string; name: string; status: string; detail: string }>;
  japan_compliance?: Record<string, {
    status: string;
    details: string[];
  }>;
}

export default function ReportsPage() {
  const [tab, setTab] = useState<"weekly" | "compliance">("weekly");
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<ReportData | null>(null);
  const [weeklyData, setWeeklyData] = useState<WeeklyReport | null>(null);
  const [weeklyLoading, setWeeklyLoading] = useState(true);
  const [lang, setLang] = useState<"en" | "ja">("ja");

  useEffect(() => {
    setLang(getLang());
  }, []);

  useEffect(() => {
    reportsApi.weekly()
      .then(setWeeklyData)
      .catch(console.error)
      .finally(() => setWeeklyLoading(false));
  }, []);

  function changeLang(l: "en" | "ja") {
    saveLang(l);
    setLang(l);
    window.dispatchEvent(new Event("aig-lang-change"));
  }

  const ja = lang === "ja";

  async function downloadFile(format: "pdf" | "excel" | "csv") {
    setLoading(true);
    try {
      const token = getToken();
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${BASE}/reports/generate?format=${format}&days=${days}`, { headers });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const ext = format === "excel" ? "xlsx" : format;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `aigis_report_${days}d.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(`Error: ${e}`);
    } finally {
      setLoading(false);
    }
  }

  async function generateReport(format: "json" | "csv") {
    setLoading(true);
    try {
      const token = getToken();
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${BASE}/reports/generate?format=${format}&days=${days}`, { headers });

      if (format === "csv") {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `aigis_report_${days}d.csv`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        const data = await res.json();
        setReport(data);
      }
    } catch (e) {
      alert(`Error: ${e}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl text-gd-text-primary" style={{ fontWeight: 580 }}>{ja ? "レポート" : "Reports"}</h1>
          <p className="text-gd-text-muted text-sm mt-1">
            {ja ? "週次セキュリティレポートとコンプライアンスレポート" : "Weekly security reports and compliance reports"}
          </p>
        </div>
        <LangToggle lang={lang} onChange={changeLang} />
      </div>

      {/* Tab switcher */}
      <div className="flex gap-1 bg-gd-elevated rounded-lg p-1 mb-6 w-fit">
        {(["weekly", "compliance"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-md text-sm transition-colors ${
              tab === t
                ? "bg-gd-accent text-white shadow-gd-inset"
                : "text-gd-text-muted hover:text-gd-text-primary"
            }`}
            style={{ fontWeight: 480 }}
          >
            {t === "weekly" ? (ja ? "週次レポート" : "Weekly Report") : (ja ? "コンプライアンス" : "Compliance")}
          </button>
        ))}
      </div>

      {/* Weekly Report Tab */}
      {tab === "weekly" && (
        <WeeklyReportSection data={weeklyData} loading={weeklyLoading} ja={ja} />
      )}

      {/* Compliance Tab */}
      {tab === "compliance" && <>
      {/* Controls */}
      <div className="bg-gd-surface rounded-xl border border-gd-subtle shadow-gd-card p-6 mb-6">
        <div className="flex flex-wrap items-end gap-4">
          <label className="block">
            <span className="text-xs text-gd-text-secondary" style={{ fontWeight: 480 }}>{ja ? "レポート期間" : "Report Period"}</span>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="block mt-1 bg-gd-input border border-gd-standard rounded-lg px-3 py-2 text-sm text-gd-text-primary focus:outline-none focus:border-gd-accent focus:shadow-gd-focus"
            >
              <option value={7}>{ja ? "過去7日間" : "Last 7 days"}</option>
              <option value={30}>{ja ? "過去30日間" : "Last 30 days"}</option>
              <option value={90}>{ja ? "過去90日間" : "Last 90 days"}</option>
              <option value={180}>{ja ? "過去180日間" : "Last 180 days"}</option>
              <option value={365}>{ja ? "過去365日間" : "Last 365 days"}</option>
            </select>
          </label>
          <button
            onClick={() => generateReport("json")}
            disabled={loading}
            className="px-5 py-2 bg-gd-accent text-white rounded-lg text-sm hover:bg-gd-accent-hover shadow-gd-inset disabled:opacity-50 transition-colors"
            style={{ fontWeight: 480 }}
          >
            {loading ? (ja ? "生成中..." : "Generating...") : (ja ? "レポート生成" : "Generate Report")}
          </button>
          <button
            onClick={() => generateReport("csv")}
            disabled={loading}
            className="px-5 py-2 bg-gd-hover text-gd-text-secondary border border-gd-subtle rounded-lg text-sm hover:bg-gd-elevated disabled:opacity-50 transition-colors"
            style={{ fontWeight: 480 }}
          >
            {ja ? "CSVダウンロード" : "Download CSV"}
          </button>
          <button
            onClick={() => downloadFile("pdf")}
            disabled={loading}
            className="px-5 py-2 bg-gd-hover text-gd-text-secondary border border-gd-subtle rounded-lg text-sm hover:bg-gd-elevated disabled:opacity-50 transition-colors"
            style={{ fontWeight: 480 }}
          >
            {ja ? "PDFダウンロード" : "Download PDF"}
          </button>
          <button
            onClick={() => downloadFile("excel")}
            disabled={loading}
            className="px-5 py-2 bg-gd-hover text-gd-text-secondary border border-gd-subtle rounded-lg text-sm hover:bg-gd-elevated disabled:opacity-50 transition-colors"
            style={{ fontWeight: 480 }}
          >
            {ja ? "Excelダウンロード" : "Download Excel"}
          </button>
        </div>
      </div>

      {/* Report Display */}
      {report && (
        <div className="space-y-6">
          {/* Executive Summary */}
          <div className="bg-gd-surface rounded-xl border border-gd-subtle shadow-gd-card p-6">
            <h2 className="text-gd-text-primary mb-4" style={{ fontWeight: 540 }}>{ja ? "エグゼクティブサマリー" : "Executive Summary"}</h2>
            <div className="text-xs text-gd-text-muted mb-4">
              {report.report_metadata.date_from.slice(0, 10)} — {report.report_metadata.date_to.slice(0, 10)}
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <MetricCard label={ja ? "総リクエスト数" : "Total Requests"} value={report.executive_summary.total_requests} />
              <MetricCard label={ja ? "安全率" : "Safety Rate"} value={`${report.executive_summary.safety_rate}%`} color="green" />
              <MetricCard label={ja ? "ブロック数" : "Threats Blocked"} value={report.executive_summary.blocked} color="red" />
              <MetricCard label={ja ? "平均リスクスコア" : "Avg Risk Score"} value={report.executive_summary.average_risk_score} />
            </div>
            <div className="grid grid-cols-3 gap-4 mt-4">
              <MetricCard label={ja ? "許可" : "Allowed"} value={report.executive_summary.allowed} color="green" />
              <MetricCard label={ja ? "レビュー待ち" : "Queued for Review"} value={report.executive_summary.queued_for_review} color="yellow" />
              <MetricCard label={ja ? "ブロック率" : "Block Rate"} value={`${report.executive_summary.block_rate}%`} color="red" />
            </div>
          </div>

          {/* Risk Distribution */}
          <div className="bg-gd-surface rounded-xl border border-gd-subtle shadow-gd-card p-6">
            <h2 className="text-gd-text-primary mb-4" style={{ fontWeight: 540 }}>{ja ? "リスクレベル分布" : "Risk Level Distribution"}</h2>
            <div className="grid grid-cols-4 gap-3">
              {(["low", "medium", "high", "critical"] as const).map((level) => {
                const levelLabel: Record<string, string> = { low: "低", medium: "中", high: "高", critical: "重大" };
                return (
                <div key={level} className={`p-3 rounded-lg text-center ${
                  level === "low" ? "bg-gd-safe-bg text-gd-safe" :
                  level === "medium" ? "bg-gd-warn-bg text-gd-warn" :
                  level === "high" ? "bg-gd-warn-bg text-gd-warn" :
                  "bg-gd-danger-bg text-gd-danger"
                }`}>
                  <p className="text-2xl" style={{ fontWeight: 580 }}>{report.risk_distribution[level] || 0}</p>
                  <p className="text-xs capitalize mt-1" style={{ fontWeight: 480 }}>{ja ? levelLabel[level] : level}</p>
                </div>
                );
              })}
            </div>
          </div>

          {/* Compliance Coverage */}
          <div className="bg-gd-surface rounded-xl border border-gd-subtle shadow-gd-card p-6">
            <h2 className="text-gd-text-primary mb-4" style={{ fontWeight: 540 }}>{ja ? "コンプライアンスカバレッジ" : "Compliance Coverage"}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-xs text-gd-text-secondary mb-2" style={{ fontWeight: 540 }}>OWASP LLM Top 10</h3>
                <div className="space-y-1.5">
                  {report.compliance_summary.owasp_coverage.map((item, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs text-gd-text-secondary">
                      <span className="text-gd-safe mt-0.5 flex-shrink-0">&#10003;</span>
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="text-xs text-gd-text-secondary mb-2" style={{ fontWeight: 540 }}>CWE/SANS Coverage</h3>
                <div className="space-y-1.5">
                  {report.compliance_summary.cwe_coverage.map((item, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs text-gd-text-secondary">
                      <span className="text-gd-safe mt-0.5 flex-shrink-0">&#10003;</span>
                      <span>{typeof item === "string" ? item : `${item.id} ${item.name}`}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-4 space-y-1.5">
                  <div className="flex items-start gap-2 text-xs text-gd-text-secondary">
                    <span className="text-gd-safe mt-0.5 flex-shrink-0">&#10003;</span>
                    <span>{ja ? "ヒューマンレビュー率" : "Human Review Rate"}: {report.compliance_summary.human_review_rate}%</span>
                  </div>
                  <div className="flex items-start gap-2 text-xs text-gd-text-secondary">
                    <span className="text-gd-safe mt-0.5 flex-shrink-0">&#10003;</span>
                    <span>{ja ? "監査証跡" : "Audit Trail"}: {report.compliance_summary.audit_trail}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Japan Compliance */}
          {report.japan_compliance && (
            <div className="bg-gd-surface rounded-xl border border-gd-subtle shadow-gd-card p-6">
              <h2 className="text-gd-text-primary mb-4" style={{ fontWeight: 540 }}>{ja ? "AI事業者ガイドライン v1.2 対応状況" : "Japan AI Regulation Compliance"}</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(report.japan_compliance).map(([key, data]: [string, any]) => (
                  <div key={key} className="border border-gd-subtle rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm text-gd-text-secondary" style={{ fontWeight: 540 }}>{key.replace(/_/g, " ").replace(/\b\w/g, (l: string) => l.toUpperCase())}</h3>
                      <span className="px-2 py-0.5 bg-gd-safe-bg text-gd-safe rounded-full text-xs" style={{ fontWeight: 480 }}>{data.status}</span>
                    </div>
                    <ul className="space-y-1">
                      {data.details.map((detail: string, i: number) => (
                        <li key={i} className="text-xs text-gd-text-muted flex items-start gap-1.5">
                          <span className="text-gd-safe mt-0.5 flex-shrink-0">&#10003;</span>
                          {detail}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {!report && !loading && (
        <div className="bg-gd-surface rounded-xl border border-gd-subtle p-12 text-center text-gd-text-muted text-sm">
          {ja ? "「レポート生成」をクリックして、選択した期間のコンプライアンスレポートを作成してください。" : "Click \"Generate Report\" to create a compliance report for the selected period."}
        </div>
      )}
      </>}
    </div>
  );
}

// === Weekly Report i18n Maps ===

const CATEGORY_JA: Record<string, string> = {
  prompt_injection: "プロンプトインジェクション",
  jailbreak: "ジェイルブレイク",
  sql_injection: "SQLインジェクション",
  command_injection: "コマンドインジェクション",
  code_injection: "コードインジェクション",
  xss_injection: "XSSインジェクション",
  pii_input: "個人情報（入力）",
  pii_leak: "個人情報漏洩",
  credential_leak: "認証情報漏洩",
  data_exfiltration: "データ窃取",
  confidential_data: "機密データ",
  system_prompt_leak: "システムプロンプト漏洩",
  output_manipulation: "出力改ざん",
  resource_abuse: "リソース悪用",
  dos_attack: "DoS攻撃",
  mcp_poisoning: "MCPポイズニング",
  mcp_tool_shadow: "MCPツールシャドウ",
  privilege_escalation: "権限昇格",
  excessive_agency: "過剰な自律性",
  supply_chain: "サプライチェーン",
};

const OWASP_JA: Record<string, string> = {
  "Prompt Injection": "プロンプトインジェクション",
  "Insecure Output Handling": "安全でない出力処理",
  "Training Data Poisoning": "学習データ汚染",
  "Model Denial of Service": "モデルDoS攻撃",
  "Supply-Chain Vulnerabilities": "サプライチェーン脆弱性",
  "Sensitive Information Disclosure": "機密情報漏洩",
  "Insecure Plugin Design": "安全でないプラグイン設計",
  "Excessive Agency": "過剰な自律性",
  "Overreliance": "過度な依存",
  "Model Theft": "モデル窃取",
};

const STATUS_JA: Record<string, string> = {
  "ACTIVE": "検出中",
  "MONITORED": "監視中",
  "PATTERN-READY": "パターン準備済",
  "NOT-COVERED": "未対応",
};

// Recommendation messages: keyword-based translation
function translateRec(msg: string, ja: boolean): string {
  if (!ja) return msg;
  return msg
    .replace(/increased (\d+)% this week/g, "が今週$1%増加しました")
    .replace(/\((\d+) -> (\d+)\)/g, "（$1 → $2）")
    .replace(/Consider reviewing detection rules(?: for this category)?\.?/g, "検出ルールの見直しを検討してください。")
    .replace(/New threat category: (\w+)/g, (_, c) => `新しい脅威カテゴリを検出: ${CATEGORY_JA[c] || c}`)
    .replace(/\((\d+) occurrences?\)\.?/g, "（$1件）。")
    .replace(/Monitor closely\.?/g, "注意して監視してください。")
    .replace(/Blocked requests doubled/g, "ブロック数が倍増しました")
    .replace(/Check for targeted attacks or false positives\.?/g, "標的型攻撃または誤検知の可能性を確認してください。")
    .replace(/Safety rate is ([\d.]+%),? below 90%\.?/g, "安全率が$1で、90%を下回っています。")
    .replace(/Review blocked requests for false positives\.?/g, "ブロックされたリクエストの誤検知を確認してください。")
    .replace(/No scans this week\.?/g, "今週のスキャンがありません。")
    .replace(/Verify Aigis integration is active\.?/g, "Aigisの統合が有効か確認してください。")
    .replace(/\((\d+)% increase\)/g, "（$1%増加）");
}

// === Weekly Report Section ===

function TrendBadge({ value, inverted }: { value: number; inverted?: boolean }) {
  const isGood = inverted ? value < -5 : value > 5;
  const isBad = inverted ? value > 5 : value < -5;
  const color = isGood ? "text-gd-safe" : isBad ? "text-gd-danger" : "text-gd-text-muted";
  const arrow = value > 5 ? "\u2191" : value < -5 ? "\u2193" : "\u2192";
  return <span className={`text-xs ${color}`} style={{ fontWeight: 500 }}>{arrow} {Math.abs(value).toFixed(0)}%</span>;
}

function WeeklyReportSection({ data, loading, ja }: { data: WeeklyReport | null; loading: boolean; ja: boolean }) {
  if (loading) return <p className="text-gd-text-muted text-sm">{ja ? "読み込み中..." : "Loading..."}</p>;
  if (!data) return <p className="text-gd-text-muted text-sm">{ja ? "データがありません" : "No data available"}</p>;

  const r = data;
  const sortedCats = Object.entries(r.category_trends).sort((a, b) => b[1].this_week - a[1].this_week);
  const owaspEntries = Object.entries(r.owasp_coverage).sort();

  return (
    <div className="space-y-6">
      {/* Period */}
      <p className="text-xs text-gd-text-muted">{r.period_start} ~ {r.period_end}</p>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gd-surface rounded-xl border border-gd-subtle p-4">
          <p className="text-xs text-gd-text-muted">{ja ? "総スキャン数" : "Total Scans"}</p>
          <p className="text-2xl text-gd-text-primary mt-1" style={{ fontWeight: 600 }}>{r.total_scans.toLocaleString()}</p>
          <TrendBadge value={r.trend_scans_pct} />
        </div>
        <div className="bg-gd-surface rounded-xl border border-gd-subtle p-4">
          <p className="text-xs text-gd-text-muted">{ja ? "ブロック数" : "Blocked"}</p>
          <p className="text-2xl text-gd-danger mt-1" style={{ fontWeight: 600 }}>{r.total_blocked}</p>
          <TrendBadge value={r.trend_blocked_pct} inverted />
        </div>
        <div className="bg-gd-surface rounded-xl border border-gd-subtle p-4">
          <p className="text-xs text-gd-text-muted">{ja ? "安全率" : "Safety Rate"}</p>
          <p className="text-2xl text-gd-safe mt-1" style={{ fontWeight: 600 }}>{(r.safety_rate * 100).toFixed(1)}%</p>
          <span className={`text-xs ${r.trend_safety_pct >= 0 ? "text-gd-safe" : "text-gd-danger"}`}>
            {r.trend_safety_pct >= 0 ? "\u2191" : "\u2193"} {Math.abs(r.trend_safety_pct).toFixed(1)}pp
          </span>
        </div>
        <div className="bg-gd-surface rounded-xl border border-gd-subtle p-4">
          <p className="text-xs text-gd-text-muted">{ja ? "レビュー待ち" : "Review"}</p>
          <p className="text-2xl text-gd-warn mt-1" style={{ fontWeight: 600 }}>{r.total_review}</p>
        </div>
      </div>

      {/* Risk Distribution */}
      <div className="bg-gd-surface rounded-xl border border-gd-subtle p-6">
        <h3 className="text-sm text-gd-text-primary mb-3" style={{ fontWeight: 540 }}>{ja ? "リスク分布" : "Risk Distribution"}</h3>
        <div className="grid grid-cols-4 gap-3">
          {(["critical", "high", "medium", "low"] as const).map((level) => {
            const colors: Record<string, string> = {
              critical: "bg-red-500/10 text-red-400",
              high: "bg-orange-500/10 text-orange-400",
              medium: "bg-yellow-500/10 text-yellow-400",
              low: "bg-green-500/10 text-green-400",
            };
            const labels: Record<string, string> = { critical: ja ? "重大" : "Critical", high: ja ? "高" : "High", medium: ja ? "中" : "Medium", low: ja ? "低" : "Low" };
            return (
              <div key={level} className={`rounded-lg p-3 text-center ${colors[level]}`}>
                <p className="text-xl" style={{ fontWeight: 600 }}>{r.risk_distribution[level] || 0}</p>
                <p className="text-xs mt-1">{labels[level]}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Category Trends */}
      {sortedCats.length > 0 && (
        <div className="bg-gd-surface rounded-xl border border-gd-subtle p-6">
          <h3 className="text-sm text-gd-text-primary mb-3" style={{ fontWeight: 540 }}>{ja ? "脅威カテゴリ（前週比）" : "Threat Categories (Week-over-Week)"}</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gd-text-muted">
                <th className="text-left pb-2">{ja ? "カテゴリ" : "Category"}</th>
                <th className="text-right pb-2">{ja ? "前週" : "Prev"}</th>
                <th className="text-right pb-2">{ja ? "今週" : "This"}</th>
                <th className="text-right pb-2">{ja ? "変化" : "Change"}</th>
              </tr>
            </thead>
            <tbody>
              {sortedCats.map(([cat, t]) => (
                <tr key={cat} className="border-t border-gd-subtle">
                  <td className="py-2 text-gd-text-secondary">{ja ? (CATEGORY_JA[cat] || cat.replace(/_/g, " ")) : cat.replace(/_/g, " ")}</td>
                  <td className="py-2 text-right text-gd-text-muted">{t.prev_week}</td>
                  <td className="py-2 text-right text-gd-text-primary" style={{ fontWeight: 520 }}>{t.this_week}</td>
                  <td className="py-2 text-right"><TrendBadge value={t.change_pct} inverted /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* OWASP Coverage */}
      <div className="bg-gd-surface rounded-xl border border-gd-subtle p-6">
        <h3 className="text-sm text-gd-text-primary mb-3" style={{ fontWeight: 540 }}>OWASP LLM Top 10</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gd-text-muted">
              <th className="text-left pb-2">ID</th>
              <th className="text-left pb-2">{ja ? "脅威" : "Threat"}</th>
              <th className="text-left pb-2">{ja ? "状態" : "Status"}</th>
              <th className="text-right pb-2">{ja ? "検出" : "Hits"}</th>
            </tr>
          </thead>
          <tbody>
            {owaspEntries.map(([oid, cov]) => {
              const statusColors: Record<string, string> = {
                active: "bg-green-500/10 text-green-400",
                monitored: "bg-blue-500/10 text-blue-400",
                "pattern-ready": "bg-gray-500/10 text-gray-400",
                "not-covered": "bg-gray-500/5 text-gray-500",
              };
              return (
                <tr key={oid} className="border-t border-gd-subtle">
                  <td className="py-2 text-gd-text-muted text-xs">{oid}</td>
                  <td className="py-2 text-gd-text-secondary">{ja ? (OWASP_JA[cov.name] || cov.name) : cov.name}</td>
                  <td className="py-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs ${statusColors[cov.protection_level] || ""}`}>
                      {ja ? (STATUS_JA[cov.protection_level.toUpperCase()] || cov.protection_level.toUpperCase()) : cov.protection_level.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-2 text-right text-gd-text-primary">{cov.detections}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Recommendations */}
      {r.recommendations.length > 0 && (
        <div className="bg-gd-surface rounded-xl border border-gd-subtle p-6">
          <h3 className="text-sm text-gd-text-primary mb-3" style={{ fontWeight: 540 }}>{ja ? "推奨アクション" : "Recommended Actions"}</h3>
          <div className="space-y-2">
            {r.recommendations.map((rec, i) => {
              const colors: Record<string, string> = {
                critical: "border-l-red-500 bg-red-500/5",
                warning: "border-l-yellow-500 bg-yellow-500/5",
                info: "border-l-blue-500 bg-blue-500/5",
              };
              return (
                <div key={i} className={`border-l-2 rounded-r-lg px-4 py-3 ${colors[rec.severity] || colors.info}`}>
                  <p className="text-sm text-gd-text-secondary">{translateRec(rec.message, ja)}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, color }: { label: string; value: number | string; color?: string }) {
  const colorClasses = color === "green" ? "text-gd-safe" : color === "red" ? "text-gd-danger" : color === "yellow" ? "text-gd-warn" : "text-gd-text-primary";
  return (
    <div className="bg-gd-elevated rounded-lg p-3">
      <p className={`text-xl ${colorClasses}`} style={{ fontWeight: 580 }}>{value}</p>
      <p className="text-xs text-gd-text-muted mt-0.5">{label}</p>
    </div>
  );
}
