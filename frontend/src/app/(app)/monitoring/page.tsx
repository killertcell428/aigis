"use client";

import { useEffect, useState } from "react";
import {
  AreaChart,
  Area,
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
import { getLang, saveLang } from "@/lib/lang";
import {
  monitorApi,
  type MonitorSnapshot,
  type AsrTrendPoint,
  type OwaspEntry,
} from "@/lib/api";

const LAYER_COLORS: Record<string, string> = {
  regex: "#7c6af6",
  similarity: "#27a644",
  decoded: "#e5a820",
  multi_turn: "#a855f7",
};

const RISK_COLORS: Record<string, string> = {
  critical: "#ef4444",
  high: "#db6d28",
  medium: "#e5a820",
  low: "#27a644",
};

const PROTECTION_BADGES: Record<string, { cls: string; en: string; ja: string }> = {
  active: { cls: "bg-gd-safe-bg text-gd-safe", en: "ACTIVE", ja: "稼働中" },
  monitored: { cls: "bg-gd-warn-bg text-gd-warn", en: "MONITORED", ja: "監視中" },
  "pattern-ready": { cls: "bg-gd-accent-glow text-gd-accent", en: "READY", ja: "準備済" },
  "not-covered": { cls: "bg-gd-elevated text-gd-text-muted", en: "—", ja: "—" },
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-gd-elevated border border-gd-subtle rounded-lg px-3 py-2 shadow-gd-elevated">
      <p className="text-xs text-gd-text-primary" style={{ fontWeight: 520 }}>{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-xs mt-0.5" style={{ color: p.color }}>
          {p.name}: {typeof p.value === "number" && p.value < 1 && p.value > 0
            ? `${(p.value * 100).toFixed(1)}%`
            : p.value}
        </p>
      ))}
    </div>
  );
};

export default function MonitoringPage() {
  const [snapshot, setSnapshot] = useState<MonitorSnapshot | null>(null);
  const [asrTrend, setAsrTrend] = useState<AsrTrendPoint[]>([]);
  const [owasp, setOwasp] = useState<Record<string, OwaspEntry>>({});
  const [pipeline, setPipeline] = useState<Record<string, { name: string; description: string }> | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);
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

  useEffect(() => {
    setLoading(true);
    Promise.all([
      monitorApi.snapshot(days * 24).catch(() => null),
      monitorApi.asrTrend(days).catch(() => []),
      monitorApi.owaspScorecard(days).catch(() => ({})),
      monitorApi.pipeline().catch(() => null),
    ])
      .then(([s, a, o, p]) => {
        setSnapshot(s);
        setAsrTrend(a);
        setOwasp(o);
        setPipeline(p?.layers ?? null);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [days]);

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-gd-text-muted text-sm">
          {ja ? "読み込み中..." : "Loading monitoring data..."}
        </p>
      </div>
    );
  }

  // Prepare chart data
  const asrChartData = asrTrend.map((t) => ({
    date: t.date.slice(5),
    ASR: Math.round(t.asr * 100),
    [ja ? "ブロック" : "Blocked"]: t.blocked,
    [ja ? "通過" : "Bypassed"]: t.bypassed,
  }));

  const owaspChartData = Object.entries(owasp)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([id, entry]) => ({
      name: id,
      [ja ? "検知数" : "Detections"]: entry.detections,
    }));

  const layerData = snapshot
    ? Object.entries(snapshot.detection_by_layer).map(([name, value]) => ({
        name,
        value,
      }))
    : [];

  const riskData = snapshot
    ? Object.entries(snapshot.risk_distribution)
        .filter(([, v]) => v > 0)
        .map(([name, value]) => ({ name, value }))
    : [];

  const catData = snapshot
    ? Object.entries(snapshot.category_counts)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 10)
        .map(([name, count]) => ({ name: name.replace(/_/g, " "), count }))
    : [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1
            className="text-2xl text-gd-text-primary tracking-tight"
            style={{ fontWeight: 580, letterSpacing: "-0.6px" }}
          >
            {ja ? "セキュリティモニタリング" : "Security Monitoring"}
          </h1>
          <p className="text-gd-text-muted text-sm mt-1">
            {ja
              ? "ai-scanner ASR追跡に着想を得た、Aigis独自のリアルタイム監視"
              : "Real-time monitoring inspired by ai-scanner ASR tracking, with Aigis's unique multi-layer defense"}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="bg-gd-input border border-gd-standard rounded-lg px-3 py-1.5 text-sm text-gd-text-primary focus:outline-none focus:border-gd-accent"
          >
            <option value={1}>{ja ? "過去24時間" : "Last 24h"}</option>
            <option value={7}>{ja ? "過去7日間" : "Last 7 days"}</option>
            <option value={30}>{ja ? "過去30日間" : "Last 30 days"}</option>
            <option value={90}>{ja ? "過去90日間" : "Last 90 days"}</option>
          </select>
          <LangToggle lang={lang} onChange={changeLang} />
        </div>
      </div>

      {/* KPI Cards */}
      {snapshot && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <StatCard
            title={ja ? "総スキャン" : "Total Scans"}
            value={snapshot.total_scans.toLocaleString()}
          />
          <StatCard
            title={ja ? "ブロック" : "Blocked"}
            value={snapshot.total_blocked}
            color="red"
          />
          <StatCard
            title={ja ? "レビュー" : "Review"}
            value={snapshot.total_review}
            color="yellow"
          />
          <StatCard
            title={ja ? "検知率" : "Detection Rate"}
            value={`${(snapshot.detection_rate * 100).toFixed(1)}%`}
            subtitle={ja ? "高いほど良い" : "Higher is better"}
            color="green"
          />
          <StatCard
            title="ASR"
            value={`${(snapshot.asr * 100).toFixed(1)}%`}
            subtitle={ja ? "低いほど良い" : "Lower is better"}
            color={snapshot.asr <= 0.05 ? "green" : snapshot.asr <= 0.2 ? "yellow" : "red"}
          />
        </div>
      )}

      {/* Multi-Layer Detection Pipeline */}
      <div className="bg-gd-surface rounded-xl border border-gd-subtle shadow-gd-card p-6">
        <h2 className="text-sm text-gd-text-secondary mb-1" style={{ fontWeight: 540 }}>
          {ja ? "多層検知パイプライン" : "Multi-Layer Detection Pipeline"}
        </h2>
        <p className="text-xs text-gd-text-muted mb-4">
          {ja
            ? "Aigisの4層防御 — スキャンだけのツールとの決定的な違い"
            : "Aigis's 4-layer defense — what makes it different from scan-only tools"}
        </p>
        <div className="grid grid-cols-4 gap-0">
          {["regex", "similarity", "decoded", "multi_turn"].map((layer, i) => (
            <div key={layer} className="relative">
              <div
                className={`bg-gd-elevated border border-gd-subtle p-4 text-center ${
                  i === 0 ? "rounded-l-xl" : i === 3 ? "rounded-r-xl" : ""
                }`}
              >
                <p className="text-xs text-gd-text-secondary" style={{ fontWeight: 540 }}>
                  L{i + 1}: {pipeline?.[layer]?.name ?? layer}
                </p>
                <p className="text-2xl text-gd-accent mt-1" style={{ fontWeight: 700 }}>
                  {snapshot?.detection_by_layer[layer]?.toLocaleString() ?? 0}
                </p>
                <p className="text-[10px] text-gd-text-dim mt-1">
                  {pipeline?.[layer]?.description ?? ""}
                </p>
              </div>
              {i < 3 && (
                <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 z-10 text-gd-accent text-lg">
                  &rarr;
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Charts Row: ASR Trend + Risk */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ASR Trend - wide */}
        <div className="lg:col-span-2 bg-gd-surface rounded-xl border border-gd-subtle p-6 shadow-gd-card">
          <h2 className="text-sm text-gd-text-secondary mb-1" style={{ fontWeight: 540 }}>
            {ja ? "ASRトレンド（Attack Success Rate）" : "ASR Trend (Attack Success Rate)"}
          </h2>
          <p className="text-xs text-gd-text-muted mb-4">
            {ja ? "ASRが低いほどディフェンスが強い" : "Lower ASR = stronger defense"}
          </p>
          {asrChartData.length === 0 ? (
            <div className="flex items-center justify-center h-[200px] text-gd-text-muted text-sm">
              {ja ? "データがありません" : "No data yet"}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={asrChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#6b6580" }} />
                <YAxis tick={{ fontSize: 11, fill: "#6b6580" }} />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="ASR"
                  stroke="#ef4444"
                  fill="rgba(239,68,68,0.1)"
                  strokeWidth={2}
                />
                <Area
                  type="monotone"
                  dataKey={ja ? "ブロック" : "Blocked"}
                  stroke="#27a644"
                  fill="rgba(39,166,68,0.1)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Risk Distribution + Layer Pie */}
        <div className="space-y-6">
          <div className="bg-gd-surface rounded-xl border border-gd-subtle p-6 shadow-gd-card">
            <h2 className="text-sm text-gd-text-secondary mb-4" style={{ fontWeight: 540 }}>
              {ja ? "リスク分布" : "Risk Distribution"}
            </h2>
            {riskData.length === 0 ? (
              <div className="flex items-center justify-center h-[100px] text-gd-text-muted text-sm">
                {ja ? "データなし" : "No data"}
              </div>
            ) : (
              <div className="space-y-2">
                {(["critical", "high", "medium", "low"] as const).map((level) => {
                  const count = snapshot?.risk_distribution[level] ?? 0;
                  const total = snapshot?.total_scans || 1;
                  const pct = (count / total) * 100;
                  const labels: Record<string, string> = { critical: "重大", high: "高", medium: "中", low: "低" };
                  return (
                    <div key={level} className="flex items-center gap-2">
                      <span className="text-xs w-8 text-right text-gd-text-muted">{ja ? labels[level] : level}</span>
                      <div className="flex-1 h-4 bg-gd-elevated rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{ width: `${Math.max(pct, count > 0 ? 3 : 0)}%`, background: RISK_COLORS[level] }}
                        />
                      </div>
                      <span className="text-xs w-8 text-gd-text-muted">{count}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="bg-gd-surface rounded-xl border border-gd-subtle p-6 shadow-gd-card">
            <h2 className="text-sm text-gd-text-secondary mb-4" style={{ fontWeight: 540 }}>
              {ja ? "検知レイヤー分布" : "Detection Layers"}
            </h2>
            {layerData.length === 0 ? (
              <div className="flex items-center justify-center h-[100px] text-gd-text-muted text-sm">
                {ja ? "データなし" : "No data"}
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={120}>
                <PieChart>
                  <Pie data={layerData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={50} strokeWidth={0}>
                    {layerData.map((entry, i) => (
                      <Cell key={i} fill={LAYER_COLORS[entry.name] ?? "#7c6af6"} />
                    ))}
                  </Pie>
                  <Legend wrapperStyle={{ fontSize: "10px", color: "#a8a3b8" }} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* OWASP LLM Top 10 Scorecard */}
      <div className="bg-gd-surface rounded-xl border border-gd-subtle shadow-gd-card">
        <div className="px-6 py-4 border-b border-gd-subtle flex items-center justify-between">
          <div>
            <h2 className="text-sm text-gd-text-secondary" style={{ fontWeight: 540 }}>
              OWASP LLM Top 10 {ja ? "スコアカード" : "Scorecard"}
            </h2>
            <p className="text-xs text-gd-text-muted mt-0.5">
              {ja ? "各脅威カテゴリの防御状況とAigis独自機能" : "Protection status per threat category with Aigis unique features"}
            </p>
          </div>
          {/* OWASP Chart */}
          {owaspChartData.length > 0 && (
            <div className="w-64 h-12">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={owaspChartData}>
                  <Bar dataKey={ja ? "検知数" : "Detections"} fill="#7c6af6" radius={[2, 2, 0, 0]} />
                  <XAxis dataKey="name" tick={{ fontSize: 8, fill: "#6b6580" }} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
        <div className="divide-y divide-[rgba(255,255,255,0.04)]">
          {Object.entries(owasp)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([id, entry]) => {
              const badge = PROTECTION_BADGES[entry.protection_level] ?? PROTECTION_BADGES["not-covered"];
              return (
                <div key={id} className="px-6 py-3 hover:bg-gd-hover transition-colors">
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-gd-text-muted font-mono w-14">{id}</span>
                    <span className="text-sm text-gd-text-primary flex-1" style={{ fontWeight: 480 }}>
                      {entry.name}
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] ${badge.cls}`} style={{ fontWeight: 520 }}>
                      {ja ? badge.ja : badge.en}
                    </span>
                    <span className="text-xs text-gd-text-muted w-16 text-right">
                      {entry.detections > 0 ? `${entry.detections} ${ja ? "件" : ""}` : "—"}
                    </span>
                  </div>
                  {entry.unique_features.length > 0 && (
                    <div className="ml-[4.5rem] mt-1.5 flex flex-wrap gap-1.5">
                      {entry.unique_features.map((feat, i) => (
                        <span
                          key={i}
                          className="inline-block px-2 py-0.5 bg-gd-accent-glow text-gd-accent rounded text-[10px]"
                          style={{ fontWeight: 480 }}
                        >
                          {feat}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
        </div>
      </div>

      {/* Category Breakdown */}
      {catData.length > 0 && (
        <div className="bg-gd-surface rounded-xl border border-gd-subtle p-6 shadow-gd-card">
          <h2 className="text-sm text-gd-text-secondary mb-4" style={{ fontWeight: 540 }}>
            {ja ? "カテゴリ別検知数" : "Detections by Category"}
          </h2>
          <ResponsiveContainer width="100%" height={Math.max(150, catData.length * 32)}>
            <BarChart data={catData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis type="number" tick={{ fontSize: 11, fill: "#6b6580" }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: "#6b6580" }} width={130} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" fill="#7c6af6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

    </div>
  );
}
