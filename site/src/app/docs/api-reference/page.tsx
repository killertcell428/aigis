"use client";

import DocsLayout from "@/components/DocsLayout";
import CodeSnippet from "@/components/ClientCodeSnippet";
import { useLanguage } from "@/contexts/LanguageContext";

const PROXY_EXAMPLE = `curl -X POST http://localhost:8000/api/v1/proxy/chat/completions \\
  -H "Authorization: Bearer aig_YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'`;

const LOGIN_EXAMPLE = `curl -X POST http://localhost:8000/api/v1/admin/login \\
  -H "Content-Type: application/json" \\
  -d '{"email": "admin@example.com", "password": "yourpassword"}'`;

function Endpoint({ method, path, auth }: { method: string; path: string; auth: string }) {
  const methodColors: Record<string, string> = {
    GET: "bg-blue-100 text-blue-700",
    POST: "bg-green-100 text-green-700",
    PUT: "bg-yellow-100 text-yellow-700",
    DELETE: "bg-red-100 text-red-700",
  };
  return (
    <div className="not-prose flex items-center gap-2 my-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
      <span className={`text-xs font-bold px-2 py-0.5 rounded font-mono ${methodColors[method] ?? "bg-gray-200 text-gray-700"}`}>
        {method}
      </span>
      <code className="text-sm font-mono text-gray-800 flex-1">{path}</code>
      <span className="text-xs text-gray-400 bg-gray-200 px-2 py-0.5 rounded">Auth: {auth}</span>
    </div>
  );
}

export default function ApiReferencePage() {
  const { lang } = useLanguage();
  const ja = lang === "ja";

  const TOC = [
    { id: "auth", label: ja ? "認証" : "Authentication" },
    { id: "proxy", label: "Proxy" },
    { id: "review", label: ja ? "レビューキュー" : "Review Queue" },
    { id: "audit", label: ja ? "監査ログ" : "Audit Logs" },
    { id: "admin", label: "Admin" },
    { id: "errors", label: ja ? "エラーコード" : "Error Codes" },
  ];

  const proxyResponses = ja ? [
    ["200", "安全 — LLMに転送済み", "OpenAI completion レスポンス"],
    ["202", "レビュー待ち", '{ "error": { "code": "queued_for_review", "review_item_id": "..." } }'],
    ["403", "ブロック", '{ "error": { "code": "request_blocked", "risk_score": N } }'],
    ["401", "無効なAPIキー", '{ "detail": "Invalid or missing API key" }'],
  ] : [
    ["200", "Safe — forwarded to LLM", "OpenAI completion response"],
    ["202", "Queued for review", '{ "error": { "code": "queued_for_review", "review_item_id": "..." } }'],
    ["403", "Blocked", '{ "error": { "code": "request_blocked", "risk_score": N } }'],
    ["401", "Invalid API key", '{ "detail": "Invalid or missing API key" }'],
  ];

  const errorCodes = ja ? [
    ["request_blocked", "入力または出力フィルターによってリクエストがブロックされた"],
    ["queued_for_review", "リクエストが人間レビュー待ち"],
    ["no_active_policy", "テナントにアクティブなポリシーが設定されていない"],
    ["upstream_error", "アップストリームLLMがエラーを返した"],
  ] : [
    ["request_blocked", "Request was blocked by the input or output filter"],
    ["queued_for_review", "Request is awaiting human review"],
    ["no_active_policy", "Tenant has no active policy configured"],
    ["upstream_error", "The upstream LLM returned an error"],
  ];

  return (
    <DocsLayout toc={TOC}>
      <h1>{ja ? "APIリファレンス" : "API Reference"}</h1>
      <p>
        {ja
          ? "すべてのエンドポイントはRESTです。ベースURLは"
          : "All endpoints are REST. The base URL is"}{" "}
        <code>http://localhost:8000</code>{" "}
        {ja ? "（ローカル開発時は" : "(or"} <code>http://localhost:8000</code>{ja ? "）です。" : " for local development)."}
      </p>

      <h2 id="auth">{ja ? "認証" : "Authentication"}</h2>
      <p>{ja ? "Aigis は2種類の認証方式を使います：" : "Aigis uses two authentication mechanisms:"}</p>
      <ul>
        <li>
          <strong>API Key</strong>{" — "}{ja ? "プロキシリクエスト用。" : "for proxy requests. Pass as"} <code>Authorization: Bearer aig_...</code>{ja ? " として渡します。APIキーはテナントスコープで " : ". API keys are tenant-scoped and start with "}<code>aig_</code>{ja ? " で始まります。" : "."}
        </li>
        <li>
          <strong>JWT Token</strong>{" — "}{ja ? "ダッシュボードAPIエンドポイント用。" : "for dashboard API endpoints. Obtain via"}{" "}
          <code>POST /api/v1/admin/login</code>{ja ? " で取得します。" : ". Pass as"} <code>Authorization: Bearer &lt;jwt&gt;</code>{ja ? " として渡します。" : "."}
        </li>
      </ul>

      <h3>{ja ? "JWTトークンの取得" : "Get JWT Token"}</h3>
      <div className="not-prose my-3">
        <CodeSnippet code={LOGIN_EXAMPLE} lang="bash" />
      </div>
      <p>{ja ? "レスポンス：" : "Response:"}</p>
      <div className="not-prose my-3">
        <CodeSnippet code={`{"access_token": "eyJ...", "token_type": "bearer"}`} lang="json" />
      </div>

      <hr />

      <h2 id="proxy">Proxy</h2>
      <Endpoint method="POST" path="/api/v1/proxy/chat/completions" auth="API Key" />
      <p>
        {ja
          ? "OpenAI互換のChat Completionsエンドポイントです。OpenAI APIとまったく同じ形式でリクエストを送信します。Aigisがリクエストをフィルタリング・ルーティングし、LLMレスポンスまたはエラーを返します。"
          : "OpenAI-compatible Chat Completions endpoint. Send requests in the exact same format as the OpenAI API. Aigis filters the request, routes it, and returns either the LLM response or an error."}
      </p>
      <div className="not-prose my-3">
        <CodeSnippet code={PROXY_EXAMPLE} lang="bash" />
      </div>

      <h4>{ja ? "レスポンス" : "Responses"}</h4>
      <div className="not-prose overflow-x-auto my-3">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-gray-50">
              <th className="text-left p-2 border border-gray-200">{ja ? "ステータス" : "Status"}</th>
              <th className="text-left p-2 border border-gray-200">{ja ? "意味" : "Meaning"}</th>
              <th className="text-left p-2 border border-gray-200">{ja ? "ボディ" : "Body"}</th>
            </tr>
          </thead>
          <tbody>
            {proxyResponses.map(([s, m, b]) => (
              <tr key={s} className="border-b border-gray-200">
                <td className="p-2 border border-gray-200 font-mono text-xs">{s}</td>
                <td className="p-2 border border-gray-200">{m}</td>
                <td className="p-2 border border-gray-200 font-mono text-xs text-gray-500 break-all">{b}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <hr />

      <h2 id="review">{ja ? "レビューキュー" : "Review Queue"}</h2>

      <Endpoint method="GET" path="/api/v1/review/queue" auth="JWT" />
      <p>{ja ? "現在のテナントのレビューアイテム一覧を取得します。" : "List review items for the current tenant. Supports"} <code>?status=pending|approved|rejected</code>{ja ? "・" : ", "}<code>limit</code>{ja ? "・" : ", and "}<code>offset</code>{ja ? " クエリパラメータに対応しています。" : " query params."}</p>

      <Endpoint method="GET" path="/api/v1/review/queue/{item_id}" auth="JWT" />
      <p>{ja ? "リクエストを含む単一のレビューアイテムを取得します。" : "Get a single review item with its associated request."}</p>

      <Endpoint method="POST" path="/api/v1/review/queue/{item_id}/decide" auth="JWT" />
      <p>{ja ? "レビューアイテムの決定を送信します。" : "Submit a decision for a review item."}</p>
      <div className="not-prose my-3">
        <CodeSnippet code={`{ "decision": "approve" | "reject" | "escalate", "note": "optional string" }`} lang="json" />
      </div>

      <hr />

      <h2 id="audit">{ja ? "監査ログ" : "Audit Logs"}</h2>

      <Endpoint method="GET" path="/api/v1/audit/logs" auth="JWT" />
      <p>
        {ja
          ? "現在のテナントの監査ログエントリ一覧を取得します。クエリパラメータ："
          : "List audit log entries for the current tenant. Query params:"}{" "}
        <code>event_type</code>{ja ? "・" : ", "}<code>severity</code>{ja ? "・" : ", "}<code>limit</code>{ja ? "（最大500）・" : " (max 500), "}<code>offset</code>.{" "}
        {ja ? "結果は" : "Results are ordered by"} <code>created_at</code>{ja ? " の降順です。" : " descending."}
      </p>

      <hr />

      <h2 id="admin">Admin</h2>

      <Endpoint method="POST" path="/api/v1/admin/login" auth="None" />
      <p>{ja ? "メール＋パスワードで認証します。JWTアクセストークンを返します。" : "Authenticate with email + password. Returns JWT access token."}</p>

      <Endpoint method="GET" path="/api/v1/admin/me" auth="JWT" />
      <p>{ja ? "現在のユーザープロファイルを取得します。" : "Get the current user profile."}</p>

      <Endpoint method="GET" path="/api/v1/admin/tenants/{tenant_id}/policies" auth="JWT" />
      <p>{ja ? "テナントのアクティブなポリシーを取得します。" : "Get the active policy for a tenant."}</p>

      <Endpoint method="PUT" path="/api/v1/admin/tenants/{tenant_id}/policies" auth="JWT" />
      <p>{ja ? "テナントのアクティブなポリシーを更新します。" : "Update the active policy for a tenant."}</p>

      <Endpoint method="POST" path="/api/v1/admin/api-keys" auth="JWT" />
      <p>{ja ? "現在のテナント用の新しいAPIキーを生成します。" : "Generate a new API key for the current tenant."}</p>

      <hr />

      <h2 id="errors">{ja ? "エラーコード" : "Error Codes"}</h2>
      <div className="not-prose overflow-x-auto my-3">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-gray-50">
              <th className="text-left p-2 border border-gray-200">{ja ? "コード" : "Code"}</th>
              <th className="text-left p-2 border border-gray-200">{ja ? "説明" : "Description"}</th>
            </tr>
          </thead>
          <tbody>
            {errorCodes.map(([code, desc]) => (
              <tr key={code} className="border-b border-gray-200">
                <td className="p-2 border border-gray-200 font-mono text-xs">{code}</td>
                <td className="p-2 border border-gray-200">{desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DocsLayout>
  );
}
