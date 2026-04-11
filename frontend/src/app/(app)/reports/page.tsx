"use client";

import { useEffect, useState } from "react";
import { getLang, saveLang } from "@/lib/lang";
import LangToggle from "@/components/LangToggle";

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
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<ReportData | null>(null);
  const [lang, setLang] = useState<"en" | "ja">("ja");

  useEffect(() => {
    setLang(getLang());
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
          <h1 className="text-2xl text-gd-text-primary" style={{ fontWeight: 580 }}>{ja ? "コンプライアンスレポート" : "Compliance Reports"}</h1>
          <p className="text-gd-text-muted text-sm mt-1">
            {ja ? "SOC2、ISO 27001、OWASP、AI事業者ガイドラインv1.2に対応したレポートを生成" : "Generate audit reports for SOC2, ISO 27001, OWASP, and Japan AI Guidelines v1.2"}
          </p>
        </div>
        <LangToggle lang={lang} onChange={changeLang} />
      </div>

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
