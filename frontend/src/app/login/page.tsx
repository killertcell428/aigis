"use client";

import { useEffect, useState } from "react";
import { authApi } from "@/lib/api";
import { getLang, saveLang } from "@/lib/lang";
import LangToggle from "@/components/LangToggle";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lang, setLang] = useState<"en" | "ja">("ja");

  useEffect(() => {
    setLang(getLang());
  }, []);

  function changeLang(l: "en" | "ja") {
    saveLang(l);
    setLang(l);
  }

  const ja = lang === "ja";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authApi.login(email, password);
      window.location.href = "/dashboard";
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gd-deep flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8 relative">
          <div className="absolute top-0 right-0">
            <LangToggle lang={lang} onChange={changeLang} />
          </div>
          <div className="w-14 h-14 rounded-2xl bg-gd-accent mx-auto flex items-center justify-center shadow-gd-inset">
            <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h1
            className="text-2xl text-gd-text-primary mt-4 tracking-tight"
            style={{ fontWeight: 580, letterSpacing: "-0.6px" }}
          >
            Aigis
          </h1>
          <p className="text-gd-text-muted text-xs mt-0.5">
            {ja ? "オープンソースAIセキュリティ" : "Open Source AI Security"}
          </p>
          <p className="text-gd-text-muted text-sm mt-1">
            {ja
              ? "AIセキュリティフィルター — ヒューマンレビューコンソール"
              : "AI Security Filter \u2014 Human Review Console"}
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-gd-surface border border-gd-subtle rounded-2xl shadow-gd-elevated p-8 space-y-5"
        >
          <div>
            <label
              className="block text-xs text-gd-text-secondary mb-1.5"
              style={{ fontWeight: 500 }}
            >
              {ja ? "メールアドレス" : "Email"}
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full bg-gd-input border border-gd-standard rounded-lg px-3 py-2.5 text-sm text-gd-text-primary placeholder-gd-text-dim focus:outline-none focus:border-gd-accent focus:shadow-gd-focus transition-all"
              placeholder="reviewer@company.com"
            />
          </div>

          <div>
            <label
              className="block text-xs text-gd-text-secondary mb-1.5"
              style={{ fontWeight: 500 }}
            >
              {ja ? "パスワード" : "Password"}
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full bg-gd-input border border-gd-standard rounded-lg px-3 py-2.5 text-sm text-gd-text-primary placeholder-gd-text-dim focus:outline-none focus:border-gd-accent focus:shadow-gd-focus transition-all"
            />
          </div>

          {error && (
            <p className="text-sm text-gd-danger bg-gd-danger-bg border border-gd-subtle rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-gd-accent hover:bg-gd-accent-hover text-white rounded-lg text-sm shadow-gd-inset disabled:opacity-50 transition-all"
            style={{ fontWeight: 540 }}
          >
            {loading
              ? (ja ? "サインイン中..." : "Signing in...")
              : (ja ? "サインイン" : "Sign In")}
          </button>
        </form>

        <p className="text-center text-gd-text-dim text-xs mt-4">
          {ja ? "OSSコアは無料でご利用いただけます" : "OSS Core is free forever"}
        </p>
      </div>
    </div>
  );
}
