"use client";

import { useEffect, useState } from "react";
import { billingApi, SubscriptionStatus, UsageStats } from "@/lib/api";
import LangToggle from "@/components/LangToggle";
import { getLang, saveLang } from "@/lib/lang";

const STATUS_COLORS: Record<string, string> = {
  active: "bg-gd-safe-bg text-gd-safe",
  trialing: "bg-gd-info-bg text-gd-accent",
  past_due: "bg-gd-danger-bg text-gd-danger",
  canceled: "bg-gd-elevated text-gd-text-secondary",
  none: "bg-gd-elevated text-gd-text-secondary",
};

export default function BillingPage() {
  const [sub, setSub] = useState<SubscriptionStatus | null>(null);
  const [usage, setUsage] = useState<UsageStats | null>(null);
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
    Promise.all([billingApi.getStatus(), billingApi.getUsage()])
      .then(([s, u]) => {
        setSub(s);
        setUsage(u);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleUpgrade = async (plan: string) => {
    try {
      const { url } = await billingApi.createCheckout(
        plan,
        `${window.location.origin}/billing?success=true`,
        `${window.location.origin}/billing`
      );
      window.location.href = url;
    } catch (err) {
      console.error("Checkout error:", err);
    }
  };

  const handleManage = async () => {
    try {
      const { url } = await billingApi.createPortal();
      window.location.href = url;
    } catch (err) {
      console.error("Portal error:", err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gd-text-muted">Loading billing info...</p>
      </div>
    );
  }

  const trialDaysLeft =
    sub?.trial_ends_at
      ? Math.max(0, Math.ceil((new Date(sub.trial_ends_at).getTime() - Date.now()) / 86_400_000))
      : null;

  const requestPct =
    usage?.monthly_requests_limit
      ? Math.min(100, Math.round((usage.monthly_requests_used / usage.monthly_requests_limit) * 100))
      : 0;

  const t = {
    en: {
      title: "Billing & Subscription",
      plan: "Current Plan",
      status: "Status",
      trialEnds: "Trial ends in",
      days: "days",
      usage: "API Usage This Month",
      team: "Team Members",
      retention: "Log Retention",
      upgrade: "Upgrade Plan",
      manage: "Manage Subscription",
      ofLimit: "of",
      requests: "requests",
      users: "users",
      unlimited: "Unlimited",
      proDesc: "Dashboard, logs, team up to 5 — $49/mo",
      bizDesc: "Compliance reports, SSO, team up to 50 — $299/mo",
      freeTitle: "Free (OSS Core)",
      freeDesc: "CLI tool, 165+ pattern detection, 6-layer defense, MCP scanner — free forever",
      retentionDays: "days",
      paymentFailed: "Payment failed. Please update your payment method.",
    },
    ja: {
      title: "課金・サブスクリプション",
      plan: "現在のプラン",
      status: "ステータス",
      trialEnds: "トライアル残り",
      days: "日",
      usage: "今月の API 使用量",
      team: "チームメンバー",
      retention: "ログ保存期間",
      upgrade: "プランをアップグレード",
      manage: "サブスクリプション管理",
      ofLimit: "/",
      requests: "リクエスト",
      users: "名",
      unlimited: "無制限",
      proDesc: "ダッシュボード、ログ閲覧、5名まで — $49/月",
      bizDesc: "コンプライアンスレポート、SSO、50名まで — $299/月",
      freeTitle: "Free (OSSコア)",
      freeDesc: "CLIツール、165+パターン検出、6層防御、MCPスキャナー — 永久無料",
      retentionDays: "日間",
      paymentFailed: "支払いに失敗しました。お支払い方法を更新してください。",
    },
  }[lang];

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl text-gd-text-primary" style={{ fontWeight: 580 }}>{t.title}</h1>
        <LangToggle lang={lang} onChange={changeLang} />
      </div>

      {/* Plan & Status */}
      <div className="bg-gd-surface border border-gd-subtle rounded-xl p-6 shadow-gd-card">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gd-text-muted">{t.plan}</p>
            <p className="text-3xl text-gd-text-primary capitalize mt-1" style={{ fontWeight: 580 }}>
              {sub?.plan || "free"}
            </p>
          </div>
          <span
            className={`px-3 py-1 rounded-full text-xs ${
              STATUS_COLORS[sub?.status || "none"]
            }`}
            style={{ fontWeight: 540 }}
          >
            {sub?.status || "none"}
          </span>
        </div>

        {trialDaysLeft !== null && sub?.status === "trialing" && (
          <div className="mt-3 text-sm text-gd-accent bg-gd-info-bg border border-gd-subtle rounded-lg px-4 py-2">
            {t.trialEnds} <strong>{trialDaysLeft}</strong> {t.days}
          </div>
        )}

        {sub?.status === "past_due" && (
          <div className="mt-3 text-sm text-gd-danger bg-gd-danger-bg border border-gd-subtle rounded-lg px-4 py-2">
            {t.paymentFailed}
          </div>
        )}
      </div>

      {/* Free Plan info */}
      {(sub?.plan || "free") === "free" && (
        <div className="bg-gd-info-bg border border-gd-subtle rounded-xl p-5">
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2 py-0.5 rounded text-xs bg-gd-safe-bg text-gd-safe border border-gd-subtle" style={{ fontWeight: 520 }}>OSS</span>
            <p className="text-sm text-gd-text-primary" style={{ fontWeight: 540 }}>{t.freeTitle}</p>
          </div>
          <p className="text-xs text-gd-text-secondary">{t.freeDesc}</p>
        </div>
      )}

      {/* Usage */}
      {usage && (
        <div className="bg-gd-surface border border-gd-subtle rounded-xl p-6 shadow-gd-card space-y-5">
          {/* Requests */}
          <div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gd-text-muted">{t.usage}</span>
              <span className="text-gd-text-secondary" style={{ fontWeight: 480 }}>
                {usage.monthly_requests_used.toLocaleString()}
                {usage.monthly_requests_limit
                  ? ` ${t.ofLimit} ${usage.monthly_requests_limit.toLocaleString()} ${t.requests}`
                  : ` ${t.requests}`}
              </span>
            </div>
            {usage.monthly_requests_limit && (
              <div className="mt-2 w-full bg-gd-elevated rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all ${
                    requestPct >= 90
                      ? "bg-gd-danger"
                      : requestPct >= 80
                      ? "bg-gd-warn"
                      : "bg-gd-accent"
                  }`}
                  style={{ width: `${requestPct}%` }}
                />
              </div>
            )}
          </div>

          {/* Team */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-gd-text-muted">{t.team}</span>
            <span className="text-gd-text-secondary" style={{ fontWeight: 480 }}>
              {usage.team_size} {t.ofLimit}{" "}
              {usage.team_limit ? `${usage.team_limit} ${t.users}` : t.unlimited}
            </span>
          </div>

          {/* Retention */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-gd-text-muted">{t.retention}</span>
            <span className="text-gd-text-secondary" style={{ fontWeight: 480 }}>
              {usage.retention_days ? `${usage.retention_days} ${t.retentionDays}` : t.unlimited}
            </span>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="space-y-3">
        {sub?.plan === "free" || sub?.plan === "pro" ? (
          <div className="bg-gd-surface border border-gd-subtle rounded-xl p-6 shadow-gd-card">
            <h2 className="text-gd-text-primary mb-4" style={{ fontWeight: 540 }}>{t.upgrade}</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {sub?.plan === "free" && (
                <button
                  onClick={() => handleUpgrade("pro")}
                  className="p-4 border-2 border-gd-subtle rounded-xl text-left hover:border-gd-accent transition-colors"
                >
                  <p className="text-gd-text-primary" style={{ fontWeight: 540 }}>Pro</p>
                  <p className="text-xs text-gd-text-muted mt-1">{t.proDesc}</p>
                </button>
              )}
              <button
                onClick={() => handleUpgrade("business")}
                className="p-4 border-2 border-gd-subtle rounded-xl text-left hover:border-purple-400 transition-colors"
              >
                <p className="text-gd-text-primary" style={{ fontWeight: 540 }}>Business</p>
                <p className="text-xs text-gd-text-muted mt-1">{t.bizDesc}</p>
              </button>
            </div>
          </div>
        ) : null}

        {(sub as any)?.stripe_customer_id !== undefined && sub?.plan !== "free" && (
          <button
            onClick={handleManage}
            className="w-full py-3 px-4 bg-gd-hover text-gd-text-secondary border border-gd-subtle rounded-lg text-sm hover:bg-gd-elevated transition-colors"
            style={{ fontWeight: 480 }}
          >
            {t.manage}
          </button>
        )}
      </div>
    </div>
  );
}
