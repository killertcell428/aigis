"use client";

import DocsLayout from "@/components/DocsLayout";
import CodeSnippet from "@/components/ClientCodeSnippet";
import { useLanguage } from "@/contexts/LanguageContext";

const BASIC = `from openai import OpenAI

client = OpenAI(
    api_key="aig_YOUR_API_KEY",
    base_url="http://localhost:8000/api/v1/proxy",
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Summarize the latest AI news."},
    ],
)
print(response.choices[0].message.content)`;

const ERROR_HANDLING = `from openai import OpenAI, APIStatusError
import sys

client = OpenAI(
    api_key="aig_YOUR_API_KEY",
    base_url="http://localhost:8000/api/v1/proxy",
)

def safe_complete(user_message: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_message}],
        )
        return response.choices[0].message.content

    except APIStatusError as e:
        body = e.response.json()
        error = body.get("error", {})
        code = error.get("code", "unknown")

        match code:
            case "request_blocked":
                score = error.get("risk_score", "?")
                return f"[BLOCKED] Risk score: {score}. Request was blocked by Aigis."

            case "queued_for_review":
                item_id = error.get("review_item_id", "?")
                return f"[QUEUED] Review ID: {item_id}. A human will review this request."

            case _:
                raise  # Re-raise unexpected errors`;

const LANGCHAIN = `from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o",
    openai_api_key="aig_YOUR_API_KEY",
    openai_api_base="http://localhost:8000/api/v1/proxy",
)

response = llm.invoke("What is the capital of France?")
print(response.content)`;

const ENV = `# .env
AI_GUARDIAN_API_KEY=aig_YOUR_API_KEY
AI_GUARDIAN_BASE_URL=http://localhost:8000/api/v1/proxy`;

const ENV_USAGE = `import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.environ["AI_GUARDIAN_API_KEY"],
    base_url=os.environ["AI_GUARDIAN_BASE_URL"],
)`;

export default function PythonIntegrationPage() {
  const { lang } = useLanguage();
  const ja = lang === "ja";

  const TOC = [
    { id: "install", label: ja ? "インストール" : "Installation" },
    { id: "basic", label: ja ? "基本的な使い方" : "Basic Usage" },
    { id: "error-handling", label: ja ? "エラーハンドリング" : "Error Handling" },
    { id: "langchain", label: "LangChain" },
    { id: "env", label: ja ? "環境変数" : "Environment Variables" },
  ];

  return (
    <DocsLayout toc={TOC}>
      <h1>{ja ? "Python インテグレーション" : "Python Integration"}</h1>
      <p>
        {ja
          ? "Aigis は"
          : "Aigis is fully compatible with the"}{" "}
        <code>openai</code>{" "}
        {ja
          ? "Python SDKと完全互換です。変更が必要なのは2つのパラメータだけです："
          : "Python SDK. You only need to change two parameters:"}{" "}
        <code>api_key</code>{ja ? " と " : " and "}<code>base_url</code>.
      </p>

      <h2 id="install">{ja ? "インストール" : "Installation"}</h2>
      <div className="not-prose my-3">
        <CodeSnippet code="pip install openai" lang="bash" />
      </div>

      <h2 id="basic">{ja ? "基本的な使い方" : "Basic Usage"}</h2>
      <div className="not-prose my-3">
        <CodeSnippet code={BASIC} lang="python" />
      </div>

      <h2 id="error-handling">{ja ? "エラーハンドリング" : "Error Handling"}</h2>
      <p>
        {ja
          ? "Aigis は標準のOpenAI形式のエラーレスポンスを返します。"
          : "Aigis returns standard OpenAI-shaped error responses. Catch"}{" "}
        <code>APIStatusError</code>{" "}
        {ja
          ? "をキャッチして"
          : "and inspect the"}{" "}
        <code>error.code</code>{" "}
        {ja ? "フィールドを確認してください：" : "field:"}
      </p>
      <div className="not-prose my-3">
        <CodeSnippet code={ERROR_HANDLING} lang="python" />
      </div>

      <h2 id="langchain">LangChain</h2>
      <p>
        {ja
          ? "LangChainは内部でOpenAI SDKを使っています。"
          : "LangChain uses the OpenAI SDK under the hood. Point"}{" "}
        <code>openai_api_base</code>{" "}
        {ja ? "をAigisに向けてください：" : "at Aigis:"}
      </p>
      <div className="not-prose my-3">
        <CodeSnippet code={LANGCHAIN} lang="python" />
      </div>

      <h2 id="env">{ja ? "環境変数" : "Environment Variables"}</h2>
      <p>{ja ? "認証情報はソースコードではなく環境変数で管理することを推奨します：" : "Best practice is to store credentials in environment variables, not in source code:"}</p>
      <div className="not-prose my-3">
        <CodeSnippet code={ENV} lang="bash" />
        <div className="mt-3" />
        <CodeSnippet code={ENV_USAGE} lang="python" />
      </div>
    </DocsLayout>
  );
}
