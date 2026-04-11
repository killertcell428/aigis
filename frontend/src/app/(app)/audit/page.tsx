"use client";

import { useEffect, useState } from "react";
import { auditApi, type AuditLog } from "@/lib/api";
import { getLang, saveLang } from "@/lib/lang";
import LangToggle from "@/components/LangToggle";

const SEVERITY_BADGE: Record<string, string> = {
  info: "bg-gd-info-bg text-gd-accent",
  warning: "bg-gd-warn-bg text-gd-warn",
  critical: "bg-gd-danger-bg text-gd-danger",
};

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [eventFilter, setEventFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [page, setPage] = useState(0);
  const PER_PAGE = 50;
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

  const load = () => {
    setLoading(true);
    auditApi
      .list({
        event_type: eventFilter || undefined,
        severity: severityFilter || undefined,
        limit: PER_PAGE,
        offset: page * PER_PAGE,
      })
      .then(setLogs)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, [eventFilter, severityFilter, page]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl text-gd-text-primary" style={{ fontWeight: 580 }}>{ja ? "監査ログ" : "Audit Logs"}</h1>
          <p className="text-gd-text-muted text-sm mt-1">
            {ja ? "すべてのフィルター判定とレビューアクションの改ざん不能な記録" : "Immutable record of all filter decisions and review actions"}
          </p>
        </div>
        <LangToggle lang={lang} onChange={changeLang} />
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder={ja ? "イベントタイプで絞り込み..." : "Filter by event type..."}
          value={eventFilter}
          onChange={(e) => {
            setEventFilter(e.target.value);
            setPage(0);
          }}
          className="bg-gd-input border border-gd-standard rounded-lg px-3 py-2 text-sm w-56 text-gd-text-primary placeholder-gd-text-dim focus:outline-none focus:border-gd-accent focus:shadow-gd-focus"
        />
        <select
          value={severityFilter}
          onChange={(e) => {
            setSeverityFilter(e.target.value);
            setPage(0);
          }}
          className="bg-gd-input border border-gd-standard rounded-lg px-3 py-2 text-sm text-gd-text-primary focus:outline-none focus:border-gd-accent focus:shadow-gd-focus"
        >
          <option value="">{ja ? "すべての重要度" : "All severities"}</option>
          <option value="info">{ja ? "情報" : "Info"}</option>
          <option value="warning">{ja ? "警告" : "Warning"}</option>
          <option value="critical">{ja ? "重大" : "Critical"}</option>
        </select>
        <button
          onClick={() => {
            setEventFilter("");
            setSeverityFilter("");
            setPage(0);
          }}
          className="px-3 py-2 text-sm border border-gd-subtle rounded-lg hover:bg-gd-elevated text-gd-text-secondary"
        >
          {ja ? "クリア" : "Clear"}
        </button>
      </div>

      {/* Table */}
      <div className="bg-gd-surface rounded-xl border border-gd-subtle shadow-gd-card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gd-elevated border-b border-gd-subtle">
            <tr>
              <th className="px-4 py-3 text-left text-xs text-gd-text-muted uppercase tracking-wide" style={{ fontWeight: 540 }}>
                {ja ? "日時" : "Time"}
              </th>
              <th className="px-4 py-3 text-left text-xs text-gd-text-muted uppercase tracking-wide" style={{ fontWeight: 540 }}>
                {ja ? "イベント" : "Event"}
              </th>
              <th className="px-4 py-3 text-left text-xs text-gd-text-muted uppercase tracking-wide" style={{ fontWeight: 540 }}>
                {ja ? "重要度" : "Severity"}
              </th>
              <th className="px-4 py-3 text-left text-xs text-gd-text-muted uppercase tracking-wide" style={{ fontWeight: 540 }}>
                {ja ? "概要" : "Summary"}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[rgba(255,255,255,0.04)]">
            {loading ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gd-text-muted">
                  {ja ? "読み込み中..." : "Loading..."}
                </td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gd-text-muted">
                  {ja ? "ログが見つかりません" : "No logs found"}
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log.id} className="hover:bg-gd-elevated transition-colors">
                  <td className="px-4 py-3 text-xs text-gd-text-muted whitespace-nowrap">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <code className="text-xs bg-gd-elevated px-1.5 py-0.5 rounded text-gd-text-secondary">
                      {log.event_type}
                    </code>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs ${
                        SEVERITY_BADGE[log.severity] ?? "bg-gd-elevated text-gd-text-secondary"
                      }`}
                      style={{ fontWeight: 540 }}
                    >
                      {log.severity}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gd-text-secondary max-w-sm truncate">
                    {log.summary}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        <div className="px-4 py-3 border-t border-gd-subtle flex items-center justify-between">
          <p className="text-xs text-gd-text-muted">
            {ja ? `${page * PER_PAGE + 1}〜${page * PER_PAGE + logs.length} 件を表示` : `Showing ${page * PER_PAGE + 1}–${page * PER_PAGE + logs.length}`}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-3 py-1.5 text-xs border border-gd-subtle rounded-lg disabled:opacity-40 hover:bg-gd-elevated text-gd-text-secondary"
            >
              {ja ? "前へ" : "Previous"}
            </button>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={logs.length < PER_PAGE}
              className="px-3 py-1.5 text-xs border border-gd-subtle rounded-lg disabled:opacity-40 hover:bg-gd-elevated text-gd-text-secondary"
            >
              {ja ? "次へ" : "Next"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
