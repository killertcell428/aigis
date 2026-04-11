"use client";

import DocsLayout from "@/components/DocsLayout";
import CodeSnippet from "@/components/ClientCodeSnippet";
import { useLanguage } from "@/contexts/LanguageContext";

const INSTALL_PYTHON = `pip install openai`;
const INSTALL_NODE = `npm install openai`;

const PYTHON_EXAMPLE = `from openai import OpenAI

client = OpenAI(
    api_key="aig_YOUR_API_KEY",          # Your Aigis key (aig_ prefix)
    base_url="http://localhost:8000/api/v1/proxy",  # Aigis endpoint
)

try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "What is the capital of France?"}],
    )
    print(response.choices[0].message.content)

except Exception as e:
    # Aigis returns standard HTTP errors
    print(f"Error: {e}")`;

const NODE_EXAMPLE = `import OpenAI from "openai";

const client = new OpenAI({
  apiKey: "aig_YOUR_API_KEY",
  baseURL: "http://localhost:8000/api/v1/proxy",
});

try {
  const response = await client.chat.completions.create({
    model: "gpt-4o",
    messages: [{ role: "user", content: "What is the capital of France?" }],
  });
  console.log(response.choices[0].message.content);
} catch (error) {
  // Aigis returns standard OpenAI error shapes
  console.error("Error:", error);
}`;

const HANDLE_RESPONSES = `import httpx
from openai import OpenAI, APIStatusError

client = OpenAI(
    api_key="aig_YOUR_API_KEY",
    base_url="http://localhost:8000/api/v1/proxy",
)

try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": user_message}],
    )
    result = response.choices[0].message.content

except APIStatusError as e:
    body = e.response.json()
    code = body.get("error", {}).get("code")

    if code == "request_blocked":
        risk_score = body["error"]["risk_score"]
        result = f"Request blocked (risk score: {risk_score})"

    elif code == "queued_for_review":
        review_id = body["error"]["review_item_id"]
        result = f"Under review (ID: {review_id}). Check back later."

    else:
        raise`;

export default function QuickstartPage() {
  const { lang } = useLanguage();
  const ja = lang === "ja";

  const TOC = [
    { id: "prerequisites", label: ja ? "前提条件" : "Prerequisites" },
    { id: "step1", label: ja ? "1. APIキーを取得" : "1. Get your API key" },
    { id: "step2", label: ja ? "2. 依存関係をインストール" : "2. Install dependencies" },
    { id: "step3", label: ja ? "3. base URLを変更" : "3. Change the base URL" },
    { id: "step4", label: ja ? "4. リクエストを送信" : "4. Make a request" },
    { id: "step5", label: ja ? "5. レスポンスを処理" : "5. Handle responses" },
    { id: "next-steps", label: ja ? "次のステップ" : "Next Steps" },
  ];

  return (
    <DocsLayout toc={TOC}>
      <h1>{ja ? "クイックスタート" : "Quickstart"}</h1>
      <p className="lead">
        {ja
          ? "Aigis の導入は5分以内で完了します。既存の OpenAI クライアントの"
          : "Integrate Aigis in under 5 minutes. All you need to change is the"}{" "}
        <code>base_url</code>{" "}
        {ja ? "を変えるだけです。" : "in your existing OpenAI client."}
      </p>

      <h2 id="prerequisites">{ja ? "前提条件" : "Prerequisites"}</h2>
      <ul>
        <li>{ja ? "Aigis アカウント（フリープランあり — カード不要）" : "An Aigis account (free tier available — no credit card required)"}</li>
        <li>{ja ? "Aigis APIキー（" : "An Aigis API key (starts with "}<code>aig_</code>{ja ? " で始まる）" : ")"}</li>
        <li>{ja ? "Python または Node.js 用の OpenAI SDK" : "The OpenAI SDK for Python or Node.js"}</li>
      </ul>

      <h2 id="step1">{ja ? "1. APIキーを取得する" : "1. Get Your API Key"}</h2>
      <p>
        {ja
          ? "サインアップ後、Aigisダッシュボードの"
          : "After signing up, go to"}{" "}
        <strong>Settings → API Keys</strong>{" "}
        {ja
          ? "で新しいキーを作成します。キーは"
          : "in the Aigis dashboard and create a new key. Copy the key — it starts with"}{" "}
        <code>aig_</code>{ja ? " で始まり、1度しか表示されません。" : " and is only shown once."}
      </p>

      <h2 id="step2">{ja ? "2. 依存関係をインストール" : "2. Install Dependencies"}</h2>
      <p>{ja ? "追加パッケージは不要です。標準の OpenAI SDK をそのまま使えます：" : "You can use the standard OpenAI SDK — no additional packages needed:"}</p>
      <div className="not-prose my-4">
        <div className="text-xs text-gray-500 mb-1 font-mono">Python</div>
        <CodeSnippet code={INSTALL_PYTHON} lang="bash" />
        <div className="text-xs text-gray-500 mb-1 mt-4 font-mono">Node.js</div>
        <CodeSnippet code={INSTALL_NODE} lang="bash" />
      </div>

      <h2 id="step3">{ja ? "3. base URL を変更する" : "3. Change the Base URL"}</h2>
      <p>
        {ja
          ? "OpenAI の"
          : "Replace the OpenAI"}{" "}
        <code>base_url</code>{" "}
        {ja
          ? "を Aigis のエンドポイントに書き換えます。それ以外は何も変える必要はありません。"
          : "with your Aigis endpoint. Everything else stays the same."}
      </p>

      <h2 id="step4">{ja ? "4. リクエストを送信する" : "4. Make a Request"}</h2>
      <div className="not-prose my-4">
        <div className="text-xs text-gray-500 mb-1 font-mono">Python</div>
        <CodeSnippet code={PYTHON_EXAMPLE} lang="python" />
        <div className="text-xs text-gray-500 mb-1 mt-4 font-mono">Node.js</div>
        <CodeSnippet code={NODE_EXAMPLE} lang="typescript" />
      </div>

      <h2 id="step5">{ja ? "5. Aigis のレスポンスを処理する" : "5. Handle Aigis Responses"}</h2>
      <p>
        {ja
          ? "Aigis は3種類の結果を返します。コードで3つすべてを処理してください："
          : "Aigis can return three different outcomes. Your code should handle all three:"}
      </p>
      <ul>
        <li><strong>200 OK</strong>{" — "}{ja ? "安全なリクエストとして転送済み。通常の OpenAI レスポンスが返ります。" : "request was safe and forwarded. Response is the normal OpenAI completion."}</li>
        <li><strong>202 Accepted</strong>{" — "}{ja ? "人間レビューのためキューに入っています。ボディに" : "request is queued for human review. Body contains"} <code>review_item_id</code>{ja ? " が含まれます。" : "."}</li>
        <li><strong>403 Forbidden</strong>{" — "}{ja ? "リクエストがブロックされました。ボディに" : "request was blocked. Body contains"} <code>risk_score</code>{ja ? " とマッチしたルールが含まれます。" : " and matched rules."}</li>
      </ul>
      <div className="not-prose my-4">
        <CodeSnippet code={HANDLE_RESPONSES} lang="python" />
      </div>

      <h2 id="next-steps">{ja ? "次のステップ" : "Next Steps"}</h2>
      <ul>
        <li><a href="/docs/concepts">{ja ? "リスクスコアリングとポリシーについて学ぶ" : "Learn about risk scoring and policies"}</a></li>
        <li><a href="/docs/api-reference">{ja ? "APIリファレンスを見る" : "Explore the full API reference"}</a></li>
        <li><a href="/docs/integrations/python">{ja ? "Pythonのサンプルをもっと見る" : "See more Python examples"}</a></li>
      </ul>
    </DocsLayout>
  );
}
