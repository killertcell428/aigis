"use client";

import CodeSnippet from "@/components/ClientCodeSnippet";
import { useLanguage } from "@/contexts/LanguageContext";

const PYTHON_CODE = `from openai import OpenAI

client = OpenAI(
    api_key="aig_your_api_key_here",  # Your Aigis API key
    base_url="http://localhost:8000/api/v1/proxy",  # <-- just change this
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What is the capital of France?"}],
)

print(response.choices[0].message.content)
# ✅ Safe requests pass through. Risky ones are blocked or queued.`;

const NODE_CODE = `import OpenAI from "openai";

const client = new OpenAI({
  apiKey: "aig_your_api_key_here",
  baseURL: "http://localhost:8000/api/v1/proxy", // <-- just change this
});

const response = await client.chat.completions.create({
  model: "gpt-4o",
  messages: [{ role: "user", content: "What is the capital of France?" }],
});

console.log(response.choices[0].message.content);
// ✅ Safe requests pass through. Risky ones are blocked or queued.`;

export default function CodeIntegrationSection() {
  const { lang } = useLanguage();
  const ja = lang === "ja";

  return (
    <section id="integration" className="py-24 bg-gray-950 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
            {ja ? "たった" : "Integrate in"}{" "}
            <span className="text-guardian-300">
              {ja ? "2行の変更" : "2 Lines of Code"}
            </span>
            {ja ? "で導入完了" : ""}
          </h2>
          <p className="text-gray-400 mt-3 text-lg max-w-xl mx-auto">
            {ja
              ? "base URL を変えるだけ。既存の OpenAI SDK をそのまま使えます。"
              : "Change the base URL. Keep using your existing OpenAI SDK. That's it."}
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 max-w-5xl mx-auto">
          <div>
            <div className="flex items-center gap-2 mb-3 text-sm text-gray-400">
              <span className="text-yellow-400">🐍</span>
              <span className="font-medium text-gray-200">Python (openai SDK)</span>
            </div>
            <CodeSnippet code={PYTHON_CODE} lang="python" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-3 text-sm text-gray-400">
              <span className="text-green-400">⬢</span>
              <span className="font-medium text-gray-200">Node.js (openai package)</span>
            </div>
            <CodeSnippet code={NODE_CODE} lang="typescript" />
          </div>
        </div>

        {/* Response examples */}
        <div className="mt-10 max-w-5xl mx-auto grid md:grid-cols-3 gap-4">
          <ResponseCard
            status="200 OK"
            statusColor="text-green-400"
            label={ja ? "安全なリクエスト" : "Safe request"}
            body={`{ "choices": [{ "message": { "content": "Paris" } }] }`}
          />
          <ResponseCard
            status="202 Accepted"
            statusColor="text-yellow-400"
            label={ja ? "レビュー待ち" : "Queued for review"}
            body={`{ "error": { "code": "queued_for_review", "review_item_id": "..." } }`}
          />
          <ResponseCard
            status="403 Forbidden"
            statusColor="text-red-400"
            label={ja ? "ブロック" : "Blocked"}
            body={`{ "error": { "code": "request_blocked", "risk_score": 95 } }`}
          />
        </div>
      </div>
    </section>
  );
}

function ResponseCard({
  status, statusColor, label, body
}: {
  status: string; statusColor: string; label: string; body: string;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <span className={`text-sm font-bold font-mono ${statusColor}`}>{status}</span>
        <span className="text-xs text-gray-500">{label}</span>
      </div>
      <code className="text-xs text-gray-400 font-mono break-all">{body}</code>
    </div>
  );
}
