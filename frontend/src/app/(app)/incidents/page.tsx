"use client";

import { useEffect, useState } from "react";
import { incidentsApi, type IncidentItem, type IncidentStats } from "@/lib/api";
import { getLang } from "@/lib/lang";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "bg-red-500/10 text-red-400 border-red-500/30",
  high: "bg-orange-500/10 text-orange-400 border-orange-500/30",
  medium: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
  low: "bg-green-500/10 text-green-400 border-green-500/30",
};

const STATUS_COLORS: Record<string, string> = {
  open: "bg-red-500/10 text-red-400",
  investigating: "bg-blue-500/10 text-blue-400",
  mitigated: "bg-yellow-500/10 text-yellow-400",
  closed: "bg-green-500/10 text-green-400",
};

const STATUS_JA: Record<string, string> = {
  open: "未対応",
  investigating: "調査中",
  mitigated: "対応済",
  closed: "クローズ",
};

const SEVERITY_JA: Record<string, string> = {
  critical: "重大",
  high: "高",
  medium: "中",
  low: "低",
};

const CATEGORY_JA: Record<string, string> = {
  prompt_injection: "プロンプトインジェクション",
  jailbreak: "ジェイルブレイク",
  sql_injection: "SQLインジェクション",
  command_injection: "コマンドインジェクション",
  pii_input: "個人情報（入力）",
  pii_leak: "個人情報漏洩",
  credential_leak: "認証情報漏洩",
  data_exfiltration: "データ窃取",
  system_prompt_leak: "システムプロンプト漏洩",
};

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<IncidentItem[]>([]);
  const [stats, setStats] = useState<IncidentStats | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [selected, setSelected] = useState<IncidentItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [note, setNote] = useState("");
  const ja = typeof window !== "undefined" ? getLang() === "ja" : true;

  useEffect(() => {
    loadData();
  }, [filter]);

  async function loadData() {
    setLoading(true);
    try {
      const params = filter !== "all" ? { status: filter } : {};
      const [list, s] = await Promise.all([
        incidentsApi.list(params),
        incidentsApi.stats(),
      ]);
      setIncidents(list);
      setStats(s);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleStatusChange(id: string, newStatus: string) {
    try {
      const updated = await incidentsApi.updateStatus(id, newStatus);
      setSelected(updated);
      loadData();
    } catch (e: any) {
      alert(e.message);
    }
  }

  async function handleResolve(id: string, resolution: string) {
    try {
      const updated = await incidentsApi.resolve(id, resolution, note || undefined);
      setSelected(updated);
      setNote("");
      loadData();
    } catch (e: any) {
      alert(e.message);
    }
  }

  async function handleAddNote(id: string) {
    if (!note.trim()) return;
    try {
      const updated = await incidentsApi.addNote(id, note);
      setSelected(updated);
      setNote("");
    } catch (e: any) {
      alert(e.message);
    }
  }

  function timeSince(dateStr: string) {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h`;
    return `${Math.floor(hours / 24)}d`;
  }

  return (
    <div className="flex gap-6 h-[calc(100vh-6rem)]">
      {/* Left panel: list */}
      <div className="w-[420px] flex-shrink-0 flex flex-col">
        <div className="mb-4">
          <h1 className="text-2xl text-gd-text-primary" style={{ fontWeight: 580 }}>
            {ja ? "インシデント" : "Incidents"}
          </h1>
          <p className="text-gd-text-muted text-sm mt-1">
            {ja ? "検出された脅威の対応状況を管理" : "Track and manage detected security threats"}
          </p>
        </div>

        {/* Stats bar */}
        {stats && (
          <div className="grid grid-cols-4 gap-2 mb-4">
            {(["open", "investigating", "mitigated", "closed"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setFilter(filter === s ? "all" : s)}
                className={`rounded-lg p-2 text-center transition-all border ${
                  filter === s ? "border-gd-accent" : "border-transparent"
                } ${STATUS_COLORS[s]}`}
              >
                <p className="text-lg" style={{ fontWeight: 600 }}>{stats[s]}</p>
                <p className="text-[10px] mt-0.5">{ja ? STATUS_JA[s] : s}</p>
              </button>
            ))}
          </div>
        )}

        {/* Incident list */}
        <div className="flex-1 overflow-y-auto space-y-2">
          {loading && <p className="text-gd-text-muted text-sm p-4">{ja ? "読み込み中..." : "Loading..."}</p>}
          {!loading && incidents.length === 0 && (
            <div className="text-center text-gd-text-muted text-sm p-8">
              {ja ? "インシデントはありません" : "No incidents found"}
            </div>
          )}
          {incidents.map((inc) => (
            <button
              key={inc.id}
              onClick={() => setSelected(inc)}
              className={`w-full text-left rounded-xl border p-4 transition-all hover:border-gd-accent ${
                selected?.id === inc.id
                  ? "bg-gd-surface border-gd-accent"
                  : "bg-gd-surface border-gd-subtle"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={`px-1.5 py-0.5 rounded text-[10px] border ${SEVERITY_COLORS[inc.severity]}`}>
                  {ja ? SEVERITY_JA[inc.severity] : inc.severity.toUpperCase()}
                </span>
                <span className={`px-1.5 py-0.5 rounded text-[10px] ${STATUS_COLORS[inc.status]}`}>
                  {ja ? STATUS_JA[inc.status] : inc.status}
                </span>
                <span className="text-[10px] text-gd-text-dim ml-auto">{inc.incident_number}</span>
              </div>
              <p className="text-sm text-gd-text-primary truncate" style={{ fontWeight: 500 }}>{inc.title}</p>
              <div className="flex items-center gap-3 mt-2 text-[10px] text-gd-text-muted">
                <span>Score: {inc.risk_score}</span>
                {inc.source_ip && <span>IP: {inc.source_ip}</span>}
                <span className="ml-auto">{timeSince(inc.detected_at)}{ja ? "前" : " ago"}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Right panel: detail */}
      <div className="flex-1 overflow-y-auto">
        {!selected ? (
          <div className="flex items-center justify-center h-full text-gd-text-muted text-sm">
            {ja ? "インシデントを選択してください" : "Select an incident to view details"}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Header */}
            <div className="bg-gd-surface rounded-xl border border-gd-subtle p-6">
              <div className="flex items-center gap-3 mb-2">
                <span className={`px-2 py-1 rounded text-xs border ${SEVERITY_COLORS[selected.severity]}`}>
                  {ja ? SEVERITY_JA[selected.severity] : selected.severity.toUpperCase()}
                </span>
                <span className={`px-2 py-1 rounded text-xs ${STATUS_COLORS[selected.status]}`}>
                  {ja ? STATUS_JA[selected.status] : selected.status}
                </span>
                <span className="text-xs text-gd-text-dim">{selected.incident_number}</span>
                {selected.sla_met !== null && (
                  <span className={`text-xs px-2 py-0.5 rounded ${selected.sla_met ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400"}`}>
                    SLA: {selected.sla_met ? (ja ? "達成" : "MET") : (ja ? "超過" : "MISSED")}
                  </span>
                )}
              </div>
              <h2 className="text-lg text-gd-text-primary" style={{ fontWeight: 560 }}>{selected.title}</h2>
              <div className="flex gap-4 mt-3 text-xs text-gd-text-muted">
                <span>{ja ? "スコア" : "Score"}: {selected.risk_score}</span>
                {selected.source_ip && <span>IP: {selected.source_ip}</span>}
                {selected.trigger_category && (
                  <span>{ja ? (CATEGORY_JA[selected.trigger_category] || selected.trigger_category) : selected.trigger_category}</span>
                )}
                <span>{ja ? "検出" : "Detected"}: {new Date(selected.detected_at).toLocaleString()}</span>
              </div>

              {/* Matched rules */}
              {selected.matched_rules.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {selected.matched_rules.map((r, i) => (
                    <span key={i} className="px-2 py-1 bg-gd-elevated rounded text-xs text-gd-text-secondary">
                      {r.rule_name} (+{r.score_delta})
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Actions */}
            {selected.status !== "closed" && (
              <div className="bg-gd-surface rounded-xl border border-gd-subtle p-4">
                <h3 className="text-xs text-gd-text-muted mb-3" style={{ fontWeight: 540 }}>
                  {ja ? "アクション" : "Actions"}
                </h3>
                <div className="flex flex-wrap gap-2">
                  {selected.status === "open" && (
                    <button onClick={() => handleStatusChange(selected.id, "investigating")}
                      className="px-3 py-1.5 bg-blue-500/10 text-blue-400 border border-blue-500/30 rounded-lg text-xs hover:bg-blue-500/20 transition-colors">
                      {ja ? "調査開始" : "Start Investigation"}
                    </button>
                  )}
                  {(selected.status === "open" || selected.status === "investigating") && (
                    <>
                      <button onClick={() => handleResolve(selected.id, "false_positive")}
                        className="px-3 py-1.5 bg-green-500/10 text-green-400 border border-green-500/30 rounded-lg text-xs hover:bg-green-500/20 transition-colors">
                        {ja ? "誤検知" : "False Positive"}
                      </button>
                      <button onClick={() => handleResolve(selected.id, "rejected")}
                        className="px-3 py-1.5 bg-red-500/10 text-red-400 border border-red-500/30 rounded-lg text-xs hover:bg-red-500/20 transition-colors">
                        {ja ? "脅威確認" : "Confirm Threat"}
                      </button>
                      <button onClick={() => handleResolve(selected.id, "blocklisted")}
                        className="px-3 py-1.5 bg-orange-500/10 text-orange-400 border border-orange-500/30 rounded-lg text-xs hover:bg-orange-500/20 transition-colors">
                        {ja ? "ブロックリスト追加" : "Add to Blocklist"}
                      </button>
                    </>
                  )}
                  {selected.status === "mitigated" && (
                    <button onClick={() => handleStatusChange(selected.id, "closed")}
                      className="px-3 py-1.5 bg-green-500/10 text-green-400 border border-green-500/30 rounded-lg text-xs hover:bg-green-500/20 transition-colors">
                      {ja ? "クローズ" : "Close Incident"}
                    </button>
                  )}
                </div>
                {/* Note input */}
                <div className="flex gap-2 mt-3">
                  <input
                    type="text"
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder={ja ? "メモを追加..." : "Add a note..."}
                    className="flex-1 bg-gd-input border border-gd-standard rounded-lg px-3 py-1.5 text-xs text-gd-text-primary placeholder-gd-text-dim focus:outline-none focus:border-gd-accent"
                  />
                  <button onClick={() => handleAddNote(selected.id)}
                    className="px-3 py-1.5 bg-gd-hover text-gd-text-secondary border border-gd-subtle rounded-lg text-xs hover:bg-gd-elevated transition-colors">
                    {ja ? "送信" : "Post"}
                  </button>
                </div>
              </div>
            )}

            {/* Resolution */}
            {selected.resolution && (
              <div className="bg-gd-surface rounded-xl border border-gd-subtle p-4">
                <h3 className="text-xs text-gd-text-muted mb-2" style={{ fontWeight: 540 }}>
                  {ja ? "解決" : "Resolution"}
                </h3>
                <span className="px-2 py-1 bg-gd-elevated rounded text-xs text-gd-text-primary">{selected.resolution}</span>
                {selected.resolution_note && (
                  <p className="text-xs text-gd-text-secondary mt-2">{selected.resolution_note}</p>
                )}
              </div>
            )}

            {/* Timeline */}
            <div className="bg-gd-surface rounded-xl border border-gd-subtle p-6">
              <h3 className="text-xs text-gd-text-muted mb-4" style={{ fontWeight: 540 }}>
                {ja ? "タイムライン" : "Timeline"}
              </h3>
              <div className="space-y-3">
                {selected.timeline.map((entry, i) => (
                  <div key={i} className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="w-2 h-2 rounded-full bg-gd-accent mt-1.5" />
                      {i < selected.timeline.length - 1 && <div className="w-px flex-1 bg-gd-subtle mt-1" />}
                    </div>
                    <div className="pb-3">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gd-text-primary" style={{ fontWeight: 500 }}>
                          {entry.action.replace(/_/g, " ").replace(/:/g, " ")}
                        </span>
                        <span className="text-[10px] text-gd-text-dim">{entry.actor}</span>
                      </div>
                      <p className="text-xs text-gd-text-muted mt-0.5">{entry.detail}</p>
                      <p className="text-[10px] text-gd-text-dim mt-0.5">
                        {new Date(entry.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
