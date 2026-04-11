"use client";

import DocsLayout from "@/components/DocsLayout";
import CodeSnippet from "@/components/ClientCodeSnippet";
import { useLanguage } from "@/contexts/LanguageContext";

const BASIC = `import OpenAI from "openai";

const client = new OpenAI({
  apiKey: "aig_YOUR_API_KEY",
  baseURL: "http://localhost:8000/api/v1/proxy",
});

const response = await client.chat.completions.create({
  model: "gpt-4o",
  messages: [
    { role: "system", content: "You are a helpful assistant." },
    { role: "user", content: "What is the capital of France?" },
  ],
});

console.log(response.choices[0].message.content);`;

const ERROR_HANDLING = `import OpenAI, { APIError } from "openai";

const client = new OpenAI({
  apiKey: process.env.AI_GUARDIAN_API_KEY,
  baseURL: process.env.AI_GUARDIAN_BASE_URL,
});

async function safeComplete(userMessage: string): Promise<string> {
  try {
    const response = await client.chat.completions.create({
      model: "gpt-4o",
      messages: [{ role: "user", content: userMessage }],
    });
    return response.choices[0].message.content ?? "";

  } catch (error) {
    if (error instanceof APIError) {
      const body = error.error as Record<string, unknown>;
      const code = (body?.code as string) ?? "unknown";

      if (code === "request_blocked") {
        return \`[BLOCKED] Risk score: \${body.risk_score}. Blocked by Aigis.\`;
      }
      if (code === "queued_for_review") {
        return \`[QUEUED] Review ID: \${body.review_item_id}. Pending human review.\`;
      }
    }
    throw error;
  }
}`;

const VERCEL_AI = `import { createOpenAI } from "@ai-sdk/openai";

const guardian = createOpenAI({
  apiKey: process.env.AI_GUARDIAN_API_KEY,
  baseURL: process.env.AI_GUARDIAN_BASE_URL,
});

// Use like any other Vercel AI SDK provider
const model = guardian("gpt-4o");`;

const ENV = `# .env.local
AI_GUARDIAN_API_KEY=aig_YOUR_API_KEY
AI_GUARDIAN_BASE_URL=http://localhost:8000/api/v1/proxy`;

export default function NodejsIntegrationPage() {
  const { lang } = useLanguage();
  const ja = lang === "ja";

  const TOC = [
    { id: "install", label: ja ? "インストール" : "Installation" },
    { id: "basic", label: ja ? "基本的な使い方" : "Basic Usage" },
    { id: "error-handling", label: ja ? "エラーハンドリング" : "Error Handling" },
    { id: "vercel-ai", label: "Vercel AI SDK" },
    { id: "env", label: ja ? "環境変数" : "Environment Variables" },
  ];

  return (
    <DocsLayout toc={TOC}>
      <h1>{ja ? "Node.js インテグレーション" : "Node.js Integration"}</h1>
      <p>
        {ja
          ? "Aigis は追加の依存関係なしに"
          : "Aigis works with the"}{" "}
        <code>openai</code>{" "}
        {ja
          ? "npm パッケージと連携します。変更するのは"
          : "npm package with zero additional dependencies. Change"}{" "}
        <code>apiKey</code>{ja ? " と " : " and "}<code>baseURL</code>{" "}
        {ja ? "の2つだけで、あとはまったく同じです。" : "— everything else is identical."}
      </p>

      <h2 id="install">{ja ? "インストール" : "Installation"}</h2>
      <div className="not-prose my-3">
        <CodeSnippet code="npm install openai" lang="bash" />
      </div>

      <h2 id="basic">{ja ? "基本的な使い方" : "Basic Usage"}</h2>
      <div className="not-prose my-3">
        <CodeSnippet code={BASIC} lang="typescript" />
      </div>

      <h2 id="error-handling">{ja ? "エラーハンドリング" : "Error Handling"}</h2>
      <p>
        {ja
          ? "openai パッケージの"
          : "Catch"}{" "}
        <code>APIError</code>{" "}
        {ja
          ? "をキャッチして"
          : "from the openai package and check the"}{" "}
        <code>error.code</code>{" "}
        {ja ? "フィールドを確認してください：" : "field:"}
      </p>
      <div className="not-prose my-3">
        <CodeSnippet code={ERROR_HANDLING} lang="typescript" />
      </div>

      <h2 id="vercel-ai">Vercel AI SDK</h2>
      <p>
        {ja
          ? "Vercel AI SDK を使っている場合は、カスタム"
          : "Using the Vercel AI SDK? Use"}{" "}
        <code>createOpenAI</code>{" "}
        {ja ? "でカスタム" : "with a custom"}{" "}
        <code>baseURL</code>{ja ? " を指定してください：" : ":"}
      </p>
      <div className="not-prose my-3">
        <CodeSnippet code={VERCEL_AI} lang="typescript" />
      </div>

      <h2 id="env">{ja ? "環境変数" : "Environment Variables"}</h2>
      <p>{ja ? "認証情報は" : "Store credentials in"} <code>.env.local</code>{ja ? "（Next.js）または" : " (Next.js) or"} <code>.env</code>{ja ? " で管理してください：" : ":"}</p>
      <div className="not-prose my-3">
        <CodeSnippet code={ENV} lang="bash" />
      </div>
    </DocsLayout>
  );
}
