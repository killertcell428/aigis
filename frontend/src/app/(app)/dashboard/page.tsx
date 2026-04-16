"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import StatCard from "@/components/StatCard";
import LangToggle from "@/components/LangToggle";
import { auditApi, billingApi, incidentsApi, type AuditLog, type UsageStats, type IncidentStats } from "@/lib/api";
import { getLang, saveLang } from "@/lib/lang";

interface Stats {
  total: number;
  blocked: number;
  queued: number;
  allowed: number;
  blockRate: string;
  safeRate: string;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-gd-elevated border border-gd-subtle rounded-lg px-3 py-2 shadow-gd-elevated">
      <p className="text-xs text-gd-text-primary" style={{ fontWeight: 520 }}>{label}</p>
      <p className="text-xs text-gd-accent mt-0.5">{payload[0].value}</p>
    </div>
  );
};

export default function DashboardPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [incStats, setIncStats] = useState<IncidentStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [lang, setLang] = useState<"en" | "ja">("ja");

  useEffect(() => {
    setLang(getLang());
  }, []);

  function changeLang(l: "en" | "ja") {
    saveLang(l);
    setLang(l);
    window.dispatchEvent(new Event("aig-lang-change"));
  }

  useEffect(() => {
    Promise.all([
      auditApi.list({ limit: 200 }),
      billingApi.getUsage().catch(() => null),
      incidentsApi.stats().catch(() => null),
    ])
      .then(([l, u, is_]) => {
        setLogs(l ?? []);
        setUsage(u);
        setIncStats(is_);
      })
      .catch((err) => {
        console.error("[Aigis Dashboard] fetch error:", err);
        if (String(err).includes("authenticated") || String(err).includes("401")) {
          localStorage.removeItem("aigis_token");
          window.location.href = "/login";
          return;
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const ja = lang === "ja";

  const stats: Stats = (() => {
    const blocked = logs.filter((l) => l.event_type.includes("blocked")).length;
    const queued = logs.filter((l) => l.event_type === "request.queued").length;
    const allowed = logs.filter((l) => l.event_type === "request.allowed").length;
    const total = logs.length;
    return {
      total,
      blocked,
      queued,
      allowed,
      blockRate: total > 0 ? ((blocked / total) * 100).toFixed(1) + "%" : "\u2014",
      safeRate: total > 0 ? ((allowed / total) * 100).toFixed(1) + "%" : "\u2014",
    };
  })();

  const eventCounts: Record<string, number> = {};
  for (const log of logs) {
    eventCounts[log.event_type] = (eventCounts[log.event_type] ?? 0) + 1;
  }
  const eventLabels: Record<string, string> = ja
    ? {
        "request.allowed": "\u8a31\u53ef",
        "request.blocked": "\u30d6\u30ed\u30c3\u30af",
        "request.queued": "\u30ec\u30d3\u30e5\u30fc\u5f85\u3061",
        "response.blocked": "\u51fa\u529b\u30d6\u30ed\u30c3\u30af",
        "review.approved": "\u627f\u8a8d",
        "review.rejected": "\u5374\u4e0b",
        "review.escalated": "\u30a8\u30b9\u30ab\u30ec",
        "review.timed_out": "\u30bf\u30a4\u30e0\u30a2\u30a6\u30c8",
      }
    : {};
  const barData = Object.entries(eventCounts).map(([name, count]) => ({
    name: eventLabels[name] ?? name.replace("request.", "").replace("review.", "rev."),
    count,
  }));

  const severityLabels: Record<string, string> = ja
    ? { info: "\u60c5\u5831", warning: "\u8b66\u544a", critical: "\u91cd\u5927" }
    : {};
  const severityCounts: Record<string, number> = {};
  for (const log of logs) {
    severityCounts[log.severity] = (severityCounts[log.severity] ?? 0) + 1;
  }
  const pieData = Object.entries(severityCounts).map(([name, value]) => ({
    name: severityLabels[name] ?? name,
    value,
  }));
  const PIE_COLORS = ["#27a644", "#e5a820", "#ef4444"];

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-gd-text-muted text-sm">
          {ja ? "\u8aad\u307f\u8fbc\u307f\u4e2d..." : "Loading dashboard..."}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1
            className="text-2xl text-gd-text-primary tracking-tight"
            style={{ fontWeight: 580, letterSpacing: "-0.6px" }}
          >
            {ja ? "\u30c0\u30c3\u30b7\u30e5\u30dc\u30fc\u30c9" : "Dashboard"}
          </h1>
          <p className="text-gd-text-muted text-sm mt-1">
            {ja
              ? "すべてのAIリクエストはリアルタイムで監視されています"
              : "Real-time monitoring of all AI requests"}
          </p>
        </div>
        <LangToggle lang={lang} onChange={changeLang} />
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title={ja ? "AI\u5229\u7528\u306e\u5b89\u5168\u7387" : "AI Safety Rate"}
          value={stats.safeRate}
          subtitle={
            ja
              ? `${stats.total}\u4ef6\u4e2d${stats.allowed}\u4ef6\u304c\u5b89\u5168\u306b\u51e6\u7406`
              : `${stats.allowed} of ${stats.total} requests safe`
          }
          color="green"
        />
        <StatCard
          title={ja ? "\u8105\u5a01\u3092\u30d6\u30ed\u30c3\u30af" : "Threats Blocked"}
          value={stats.blocked}
          subtitle={
            ja
              ? `\u30d6\u30ed\u30c3\u30af\u7387 ${stats.blockRate}`
              : `${stats.blockRate} block rate`
          }
          color="red"
        />
        <StatCard
          title={ja ? "\u3042\u306a\u305f\u306e\u5224\u65ad\u3092\u5f85\u3063\u3066\u3044\u307e\u3059" : "Pending Review"}
          value={stats.queued}
          color="yellow"
        />
        <StatCard
          title={ja ? "\u5b89\u5168\u306b\u901a\u904e" : "Allowed"}
          value={stats.allowed}
        />
      </div>

      {/* Incident stats */}
      {incStats && incStats.total > 0 && (
        <div className="bg-gd-surface border border-gd-subtle rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm text-gd-text-primary" style={{ fontWeight: 540 }}>
              {ja ? "インシデント状況" : "Incident Status"}
            </h3>
            <a href="/incidents" className="text-xs text-gd-accent hover:underline">
              {ja ? "すべて見る" : "View all"}
            </a>
          </div>
          <div className="grid grid-cols-4 gap-3">
            <div className="text-center">
              <p className="text-lg text-red-400" style={{ fontWeight: 600 }}>{incStats.open}</p>
              <p className="text-[10px] text-gd-text-muted">{ja ? "未対応" : "Open"}</p>
            </div>
            <div className="text-center">
              <p className="text-lg text-blue-400" style={{ fontWeight: 600 }}>{incStats.investigating}</p>
              <p className="text-[10px] text-gd-text-muted">{ja ? "調査中" : "Investigating"}</p>
            </div>
            <div className="text-center">
              <p className="text-lg text-yellow-400" style={{ fontWeight: 600 }}>{incStats.mitigated}</p>
              <p className="text-[10px] text-gd-text-muted">{ja ? "対応済" : "Mitigated"}</p>
            </div>
            <div className="text-center">
              <p className="text-lg text-green-400" style={{ fontWeight: 600 }}>{incStats.closed}</p>
              <p className="text-[10px] text-gd-text-muted">{ja ? "クローズ" : "Closed"}</p>
            </div>
          </div>
        </div>
      )}

      {/* Plan usage */}
      {usage && usage.plan !== "free" && (
        <div className="bg-gd-surface border border-gd-subtle rounded-xl px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gd-accent-glow flex items-center justify-center">
              <svg
                className="w-4 h-4 text-gd-accent"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.8}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
                />
              </svg>
            </div>
            <div>
              <p
                className="text-sm text-gd-text-primary capitalize"
                style={{ fontWeight: 540 }}
              >
                {usage.plan} Plan
              </p>
              <p className="text-xs text-gd-text-muted">
                {usage.monthly_requests_used.toLocaleString()}
                {usage.monthly_requests_limit
                  ? ` / ${usage.monthly_requests_limit.toLocaleString()} requests`
                  : " requests"}
              </p>
            </div>
          </div>
          {usage.monthly_requests_limit && (
            <div className="w-32">
              <div className="w-full bg-gd-elevated rounded-full h-1.5">
                <div
                  className={`h-1.5 rounded-full transition-all ${
                    usage.monthly_requests_used / usage.monthly_requests_limit >= 0.9
                      ? "bg-gd-danger"
                      : usage.monthly_requests_used / usage.monthly_requests_limit >= 0.8
                      ? "bg-gd-warn"
                      : "bg-gd-accent"
                  }`}
                  style={{
                    width: `${Math.min(
                      100,
                      (usage.monthly_requests_used / usage.monthly_requests_limit) * 100
                    )}%`,
                  }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Governance message */}
      <div className="bg-gd-info-bg border border-gd-subtle rounded-xl px-5 py-4 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gd-accent-glow flex-shrink-0 flex items-center justify-center">
          <svg
            className="w-4 h-4 text-gd-accent"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
          </svg>
        </div>
        <div>
          <p className="text-sm text-gd-info" style={{ fontWeight: 540 }}>
            {ja ? "Aigis v1.3.1 が稼働中" : "Aigis v1.3.1 Active"}
          </p>
          <p className="text-xs text-gd-text-secondary mt-0.5">
            {ja
              ? "165+パターン・6層防御（CaMeL Capabilities / AEP / Safety Verifier含む）でプロンプトインジェクション・MCPセキュリティ脅威を自動検出。OSSコアは無料でご利用いただけます。"
              : "165+ patterns with 6-layer defense (incl. CaMeL Capabilities, AEP, Safety Verifier) detect prompt injection & MCP security threats. OSS Core is free forever."}
          </p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gd-surface rounded-xl border border-gd-subtle p-6 shadow-gd-card">
          <h2
            className="text-sm text-gd-text-secondary mb-4"
            style={{ fontWeight: 540 }}
          >
            {ja ? "\u30a4\u30d9\u30f3\u30c8\u5185\u8a33" : "Event Breakdown"}
          </h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={barData}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255,255,255,0.06)"
              />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 11, fill: "#6b6580" }}
              />
              <YAxis tick={{ fontSize: 11, fill: "#6b6580" }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" fill="#7c6af6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gd-surface rounded-xl border border-gd-subtle p-6 shadow-gd-card">
          <h2
            className="text-sm text-gd-text-secondary mb-4"
            style={{ fontWeight: 540 }}
          >
            {ja ? "\u91cd\u8981\u5ea6\u5206\u5e03" : "Severity Distribution"}
          </h2>
          {pieData.length === 0 ? (
            <div className="flex items-center justify-center h-[220px] text-gd-text-muted text-sm">
              {ja ? "\u30c7\u30fc\u30bf\u304c\u3042\u308a\u307e\u305b\u3093" : "No data yet"}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  strokeWidth={0}
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                >
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Legend
                  wrapperStyle={{ fontSize: "11px", color: "#a8a3b8" }}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Recent events */}
      <div className="bg-gd-surface rounded-xl border border-gd-subtle shadow-gd-card">
        <div className="px-6 py-4 border-b border-gd-subtle">
          <h2
            className="text-sm text-gd-text-secondary"
            style={{ fontWeight: 540 }}
          >
            {ja ? "\u6700\u8fd1\u306e\u30a4\u30d9\u30f3\u30c8" : "Recent Events"}
          </h2>
        </div>
        <div className="divide-y divide-[rgba(255,255,255,0.04)]">
          {logs.slice(0, 10).map((log) => (
            <div
              key={log.id}
              className="px-6 py-3 flex items-start gap-4 hover:bg-gd-hover transition-colors"
            >
              <span
                className={`mt-1.5 h-2 w-2 rounded-full flex-shrink-0 ${
                  log.severity === "critical"
                    ? "bg-gd-danger"
                    : log.severity === "warning"
                    ? "bg-gd-warn"
                    : "bg-gd-safe"
                }`}
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gd-text-primary truncate">
                  {log.summary}
                </p>
                <p className="text-xs text-gd-text-dim mt-0.5">
                  {eventLabels[log.event_type] ?? log.event_type}
                </p>
              </div>
              <time className="text-xs text-gd-text-dim flex-shrink-0 font-mono">
                {new Date(log.created_at).toLocaleTimeString()}
              </time>
            </div>
          ))}
          {logs.length === 0 && (
            <div className="px-6 py-8 text-center text-gd-text-muted text-sm">
              {ja
                ? "\u30a4\u30d9\u30f3\u30c8\u306f\u307e\u3060\u3042\u308a\u307e\u305b\u3093\u3002Playground\u304b\u3089\u30d7\u30ed\u30f3\u30d7\u30c8\u3092\u9001\u4fe1\u3057\u3066\u307f\u3066\u304f\u3060\u3055\u3044\u3002"
                : "No events yet. Send a request through the Playground to get started."}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
