"use client";

import { useState, useEffect } from "react";
import { authApi } from "@/lib/api";
import { getLang, saveLang } from "@/lib/lang";
import LangToggle from "@/components/LangToggle";

export default function SettingsPage() {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
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

  const t = ja ? {
    title: "設定",
    subtitle: "テナント設定とAPIキー管理",
    apiKeyTitle: "プロキシAPIキー",
    apiKeyDesc: "Aigisプロキシへのリクエスト認証に使用するキーです。AuthorizationヘッダーにBearerトークンとして設定してください。",
    generate: "新しいAPIキーを生成",
    generating: "生成中...",
    keyWarning: "このキーは再表示されません。今すぐコピーしてください。",
    proxyTitle: "プロキシの使い方",
    proxyDesc: "既存のOpenAI base URLをAigisプロキシに置き換えるだけで利用できます：",
    slackTitle: "Slack通知",
    slackDesc: "脅威がブロックされた際にSlackでリアルタイム通知を受け取れます。",
    slackSave: "保存",
    slackSaved: "Slack Webhook URLを保存しました",
    logout: "ログアウト",
  } : {
    title: "Settings",
    subtitle: "Tenant settings and API key management",
    apiKeyTitle: "Proxy API Key",
    apiKeyDesc: "Use this key to authenticate requests to the Aigis proxy. Pass it as a Bearer token in the Authorization header.",
    generate: "Generate New API Key",
    generating: "Generating...",
    keyWarning: "This key will not be shown again. Copy it now.",
    proxyTitle: "Proxy Usage",
    proxyDesc: "Replace your existing OpenAI base URL with the Aigis proxy:",
    slackTitle: "Slack Notifications",
    slackDesc: "Get real-time alerts in Slack when threats are blocked.",
    slackSave: "Save",
    slackSaved: "Slack webhook saved!",
    logout: "Log Out",
  };

  async function generateKey() {
    setGenerating(true);
    try {
      const res = await fetch("/api/v1/admin/api-keys/generate", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("aigis_token")}`,
        },
      });
      const data = await res.json();
      setApiKey(data.api_key);
    } catch (e) {
      alert(`Error: ${e}`);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl text-gd-text-primary" style={{ fontWeight: 580 }}>{t.title}</h1>
          <p className="text-gd-text-muted text-sm mt-1">
            {t.subtitle}
          </p>
        </div>
        <LangToggle lang={lang} onChange={changeLang} />
      </div>

      {/* API Key section */}
      <div className="bg-gd-surface rounded-xl border border-gd-subtle shadow-gd-card p-6 space-y-4">
        <h2 className="text-gd-text-primary" style={{ fontWeight: 540 }}>{t.apiKeyTitle}</h2>
        <p className="text-sm text-gd-text-muted">
          {t.apiKeyDesc}{" "}
          <code className="bg-gd-elevated px-1 rounded text-xs">
            POST /api/v1/proxy/chat/completions
          </code>
        </p>

        {apiKey ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2 p-3 bg-gd-safe-bg border border-gd-subtle rounded-lg">
              <code className="text-sm text-gd-safe break-all">{apiKey}</code>
            </div>
            <p className="text-xs text-gd-danger" style={{ fontWeight: 480 }}>
              {t.keyWarning}
            </p>
          </div>
        ) : (
          <button
            onClick={generateKey}
            disabled={generating}
            className="px-4 py-2 bg-gd-accent hover:bg-gd-accent-hover text-white rounded-lg text-sm shadow-gd-inset disabled:opacity-50"
            style={{ fontWeight: 480 }}
          >
            {generating ? t.generating : t.generate}
          </button>
        )}
      </div>

      {/* Proxy usage */}
      <div className="bg-gd-surface rounded-xl border border-gd-subtle shadow-gd-card p-6 space-y-4 mt-4">
        <h2 className="text-gd-text-primary" style={{ fontWeight: 540 }}>{t.proxyTitle}</h2>
        <p className="text-sm text-gd-text-muted">
          {t.proxyDesc}
        </p>
        <pre className="bg-gd-deep text-green-400 rounded-lg p-4 text-xs overflow-x-auto">
{`# Python example
import openai
client = openai.OpenAI(
    api_key="YOUR_GUARDIAN_API_KEY",
    base_url="https://your-domain.com/api/v1/proxy"
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)`}
        </pre>
      </div>

      {/* Slack Integration */}
      <div className="bg-gd-surface rounded-xl border border-gd-subtle shadow-gd-card p-6 space-y-4 mt-4">
        <h2 className="text-gd-text-primary" style={{ fontWeight: 540 }}>{t.slackTitle}</h2>
        <p className="text-sm text-gd-text-muted">
          {t.slackDesc}{" "}
          <a
            href="https://api.slack.com/messaging/webhooks"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gd-accent underline"
          >
            Incoming Webhook URL
          </a>{" "}
        </p>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            const form = e.target as HTMLFormElement;
            const input = form.elements.namedItem("slack_url") as HTMLInputElement;
            try {
              await fetch("/api/v1/settings/notifications", {
                method: "PUT",
                headers: {
                  "Content-Type": "application/json",
                  Authorization: `Bearer ${localStorage.getItem("aigis_token")}`,
                },
                body: JSON.stringify({
                  slack_webhook_url: input.value || null,
                  notify_on_block: true,
                }),
              });
              alert(t.slackSaved);
            } catch (err) {
              alert(`Error: ${err}`);
            }
          }}
          className="flex gap-2"
        >
          <input
            name="slack_url"
            type="url"
            placeholder="https://hooks.slack.com/services/..."
            className="flex-1 px-3 py-2 bg-gd-input border border-gd-standard rounded-lg text-sm text-gd-text-primary placeholder-gd-text-dim focus:outline-none focus:border-gd-accent focus:shadow-gd-focus"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-gd-accent hover:bg-gd-accent-hover text-white rounded-lg text-sm shadow-gd-inset"
            style={{ fontWeight: 480 }}
          >
            {t.slackSave}
          </button>
        </form>
      </div>

      {/* Logout */}
      <div className="mt-6">
        <button
          onClick={() => {
            authApi.logout();
            window.location.href = "/login";
          }}
          className="px-4 py-2 bg-gd-hover text-gd-text-secondary border border-gd-subtle rounded-lg text-sm hover:bg-gd-elevated"
        >
          {t.logout}
        </button>
      </div>
    </div>
  );
}
