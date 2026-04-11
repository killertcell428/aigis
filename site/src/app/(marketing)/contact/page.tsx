"use client";

import { useState } from "react";
import { useLanguage } from "@/contexts/LanguageContext";

export default function ContactPage() {
  const { lang } = useLanguage();
  const ja = lang === "ja";
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setStatus("loading");
    const form = e.currentTarget;
    const data = Object.fromEntries(new FormData(form));

    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setStatus("success");
    } catch {
      setStatus("error");
    }
  };

  if (status === "success") {
    return (
      <div className="min-h-[60vh] flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="text-5xl mb-4">✓</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            {ja ? "送信完了" : "Message Sent"}
          </h1>
          <p className="text-gray-500">
            {ja
              ? "お問い合わせありがとうございます。2営業日以内にご返信いたします。"
              : "Thank you for reaching out. We'll get back to you within 2 business days."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="bg-gray-950 text-white py-16 text-center">
        <h1 className="text-4xl font-extrabold tracking-tight mb-3">
          {ja ? "お問い合わせ" : "Contact Sales"}
        </h1>
        <p className="text-gray-400 text-lg max-w-xl mx-auto">
          {ja
            ? "Enterprise プランのご相談、オンプレミス導入、カスタム要件についてお気軽にお問い合わせください。"
            : "Get in touch about Enterprise plans, on-premises deployment, or custom requirements."}
        </p>
      </div>

      <section className="py-16 bg-gray-50">
        <div className="max-w-lg mx-auto px-4">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {ja ? "お名前" : "Name"} *
              </label>
              <input
                name="name"
                required
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-sm focus:ring-2 focus:ring-guardian-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {ja ? "メールアドレス" : "Work Email"} *
              </label>
              <input
                name="email"
                type="email"
                required
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-sm focus:ring-2 focus:ring-guardian-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {ja ? "会社名" : "Company"}
              </label>
              <input
                name="company"
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-sm focus:ring-2 focus:ring-guardian-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {ja ? "業種" : "Industry"}
              </label>
              <select
                name="industry"
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-sm focus:ring-2 focus:ring-guardian-500 focus:border-transparent bg-white"
              >
                <option value="">{ja ? "選択してください" : "Select..."}</option>
                <option value="finance">{ja ? "金融" : "Finance"}</option>
                <option value="healthcare">{ja ? "ヘルスケア" : "Healthcare"}</option>
                <option value="government">{ja ? "政府・自治体" : "Government"}</option>
                <option value="manufacturing">{ja ? "製造業" : "Manufacturing"}</option>
                <option value="legal">{ja ? "法律" : "Legal"}</option>
                <option value="technology">{ja ? "テクノロジー" : "Technology"}</option>
                <option value="other">{ja ? "その他" : "Other"}</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {ja ? "チーム規模" : "Team Size"}
              </label>
              <select
                name="teamSize"
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-sm focus:ring-2 focus:ring-guardian-500 focus:border-transparent bg-white"
              >
                <option value="">{ja ? "選択してください" : "Select..."}</option>
                <option value="1-10">1-10</option>
                <option value="11-50">11-50</option>
                <option value="51-200">51-200</option>
                <option value="201-1000">201-1,000</option>
                <option value="1001+">1,001+</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {ja ? "ご要望・ご質問" : "Message"} *
              </label>
              <textarea
                name="message"
                required
                rows={4}
                placeholder={ja
                  ? "例：オンプレミス導入、FISC対応、カスタムポリシーについて相談したい"
                  : "e.g., On-premises deployment, FISC compliance, custom policy requirements"}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-sm focus:ring-2 focus:ring-guardian-500 focus:border-transparent resize-none"
              />
            </div>

            <button
              type="submit"
              disabled={status === "loading"}
              className="w-full btn-primary py-3 text-base disabled:opacity-50"
            >
              {status === "loading"
                ? (ja ? "送信中..." : "Sending...")
                : (ja ? "送信する" : "Send Message")}
            </button>

            {status === "error" && (
              <p className="text-red-500 text-sm text-center">
                {ja ? "送信に失敗しました。もう一度お試しください。" : "Failed to send. Please try again."}
              </p>
            )}
          </form>

          <div className="mt-8 text-center text-sm text-gray-500">
            {ja ? "または直接メール：" : "Or email us directly: "}
            <a href="mailto:ueda.bioinfo.base01@gmail.com" className="text-guardian-600 hover:underline">
              ueda.bioinfo.base01@gmail.com
            </a>
          </div>
        </div>
      </section>
    </>
  );
}
