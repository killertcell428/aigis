"use client";

import DocsLayout from "@/components/DocsLayout";
import { useLanguage } from "@/contexts/LanguageContext";

export default function ConceptsPage() {
  const { lang } = useLanguage();
  const ja = lang === "ja";

  const TOC = [
    { id: "filter-engine", label: ja ? "フィルターエンジン" : "Filter Engine" },
    { id: "input-filter", label: ja ? "入力フィルター" : "Input Filter", level: 3 },
    { id: "output-filter", label: ja ? "出力フィルター" : "Output Filter", level: 3 },
    { id: "risk-scoring", label: ja ? "リスクスコアリング" : "Risk Scoring" },
    { id: "score-levels", label: ja ? "スコアレベル" : "Score Levels", level: 3 },
    { id: "routing", label: ja ? "リクエストルーティング" : "Request Routing" },
    { id: "hitl", label: "Human-in-the-Loop" },
    { id: "sla", label: ja ? "SLA・フォールバック" : "SLA & Fallback", level: 3 },
    { id: "capabilities", label: ja ? "Capability-Based Access Control" : "Capability-Based Access Control" },
    { id: "aep", label: ja ? "Atomic Execution Pipeline (AEP)" : "Atomic Execution Pipeline (AEP)" },
    { id: "safety-verifier", label: ja ? "Safety Verifier" : "Safety Verifier" },
    { id: "policy-engine", label: ja ? "ポリシーエンジン" : "Policy Engine" },
    { id: "multi-tenancy", label: ja ? "マルチテナンシー" : "Multi-Tenancy" },
  ];

  const scoreLevels = ja ? [
    ["Low（低）", "0–30", "自動許可 → LLMに転送"],
    ["Medium（中）", "31–60", "人間レビューキューへ"],
    ["High（高）", "61–80", "人間レビューキューへ（優先）"],
    ["Critical（重大）", "81–100", "自動ブロック → 403を返す"],
  ] : [
    ["Low", "0–30", "Auto-allow → forward to LLM"],
    ["Medium", "31–60", "Queue for human review"],
    ["High", "61–80", "Queue for human review (priority)"],
    ["Critical", "81–100", "Auto-block → 403 returned"],
  ];

  return (
    <DocsLayout toc={TOC}>
      <h1>{ja ? "コアコンセプト" : "Core Concepts"}</h1>
      <p>
        {ja
          ? "このページでは、Aigis の主要コンセプトを説明します：フィルターエンジン・リスクスコアリング・ルーティングロジック・人間レビューキュー・ポリシー設定。"
          : "This page explains the key concepts behind Aigis: the filter engine, risk scoring system, routing logic, human review queue, and policy configuration."}
      </p>

      <h2 id="filter-engine">{ja ? "フィルターエンジン" : "Filter Engine"}</h2>
      <p>
        {ja
          ? "フィルターエンジンはAigisの中核です。コンパイル済み正規表現のライブラリを使ってテキストコンテンツを脅威パターンでスキャンします。各ルールには「スコアデルタ」が関連付けられており、複数マッチは蓄積されますが、カテゴリごとにキャップされます。最終的なリスクスコアは100を上限とします。"
          : "The Filter Engine is the heart of Aigis. It scans text content for threat patterns using a library of compiled regular expressions, each associated with a score delta. Multiple matches accumulate, but per-category scores are capped to prevent any single category from dominating. The total risk score is clamped to 100."}
      </p>

      <h3 id="input-filter">{ja ? "入力フィルター" : "Input Filter"}</h3>
      <p>
        {ja
          ? "LLMに届く前に、すべての受信リクエストに適用されます。以下のカテゴリで全メッセージ（マルチパートを含む）をスキャンします："
          : "Applied to every incoming request before it reaches the LLM. Scans all message content (including multipart messages) across these categories:"}
      </p>
      <ul>
        <li><strong>{ja ? "プロンプトインジェクション" : "Prompt Injection"}</strong>{" — "}{ja ? "「前の指示を無視して」・DANジェイルブレイク・システムプロンプト漏洩" : "\"ignore previous instructions\", DAN jailbreaks, system prompt leakage"}</li>
        <li><strong>SQL Injection</strong>{" — "}{ja ? "UNION SELECT・DROP TABLE・コメントインジェクション" : "UNION SELECT, DROP TABLE, comment injection"}</li>
        <li><strong>{ja ? "コマンドインジェクション" : "Command Injection"}</strong>{" — "}{ja ? "シェルメタ文字・" : "shell metacharacters, "}<code>; rm -rf</code>{ja ? "・curl流出パターン" : ", curl exfiltration patterns"}</li>
        <li><strong>{ja ? "データ流出" : "Data Exfiltration"}</strong>{" — "}{ja ? "認証情報・設定ファイル・環境変数の印刷を要求するリクエスト" : "requests to print credentials, config files, or environment variables"}</li>
      </ul>

      <h3 id="output-filter">{ja ? "出力フィルター" : "Output Filter"}</h3>
      <p>
        {ja
          ? "呼び出し元に返される前に、すべてのLLMレスポンスに適用されます。以下を検出します："
          : "Applied to every LLM response before it is returned to the caller. Detects:"}
      </p>
      <ul>
        <li><strong>{ja ? "PIIリーク" : "PII Leaks"}</strong>{" — "}{ja ? "クレジットカード番号（Luhnチェック）・SSN・メールアドレス" : "credit card numbers (Luhn-checked), SSNs, email addresses"}</li>
        <li><strong>{ja ? "シークレットリーク" : "Secret Leaks"}</strong>{" — "}OpenAI APIキー（<code>sk-...</code>）{ja ? "・AWSアクセスキー・汎用トークン" : ", AWS access keys, generic tokens"}</li>
        <li><strong>{ja ? "有害コンテンツ" : "Harmful Content"}</strong>{" — "}{ja ? "レスポンスに有害な指示が含まれるパターン" : "patterns suggesting harmful instructions in responses"}</li>
      </ul>
      <p>
        {ja
          ? "出力フィルターがレスポンスにフラグを立てると、入力が安全だったとしてもブロックされます。呼び出し元には"
          : "If the output filter flags a response, it is blocked even if the input was safe. The caller receives a 403 with"}{" "}
        <code>&quot;code&quot;: &quot;request_blocked&quot;</code>{ja ? " を含む403が返ります。" : "."}
      </p>

      <h2 id="risk-scoring">{ja ? "リスクスコアリング" : "Risk Scoring"}</h2>
      <p>
        {ja
          ? "すべてのリクエストとレスポンスには、0〜100の"
          : "Every request and response receives a"}{" "}
        <strong>{ja ? "リスクスコア" : "risk score"}</strong>{ja ? "と、対応する" : " between 0 and 100 and a corresponding"}{" "}
        <strong>{ja ? "リスクレベル" : "risk level"}</strong>{ja ? "が付与されます：" : ":"}
      </p>

      <h3 id="score-levels">{ja ? "スコアレベル" : "Score Levels"}</h3>
      <div className="not-prose overflow-x-auto my-4">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-gray-50">
              <th className="text-left p-3 border border-gray-200">{ja ? "レベル" : "Level"}</th>
              <th className="text-left p-3 border border-gray-200">{ja ? "スコア範囲" : "Score Range"}</th>
              <th className="text-left p-3 border border-gray-200">{ja ? "デフォルトアクション" : "Default Action"}</th>
            </tr>
          </thead>
          <tbody>
            {scoreLevels.map(([level, range, action]) => (
              <tr key={level} className="border-b border-gray-200">
                <td className="p-3 border border-gray-200 font-semibold">{level}</td>
                <td className="p-3 border border-gray-200 font-mono text-xs">{range}</td>
                <td className="p-3 border border-gray-200 text-gray-600">{action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p>
        {ja
          ? "閾値（"
          : "The thresholds ("}<code>auto_allow_threshold</code>{ja ? " と " : " and "}<code>auto_block_threshold</code>
        {ja
          ? "）はポリシーエンジンでテナントごとに設定できます。"
          : ") are configurable per tenant via the Policy Engine."}
      </p>

      <h2 id="routing">{ja ? "リクエストルーティング" : "Request Routing"}</h2>
      <p>{ja ? "リスクスコアと設定済みポリシーに基づき、すべてのリクエストは3つのいずれかにルーティングされます：" : "Based on the risk score and configured policy, every request is routed to one of three paths:"}</p>
      <ul>
        <li><strong>{ja ? "許可" : "Allow"}</strong>{" — "}{ja ? "アップストリームLLMに転送。レスポンスは返す前にフィルタリングされます。" : "forwarded to the upstream LLM. Response is filtered before return."}</li>
        <li><strong>{ja ? "キュー" : "Queue"}</strong>{" — "}{ja ? "レビューキューに保留。呼び出し元には即座に202が返り、ボディに" : "held in the review queue. A 202 response is returned immediately to the caller, containing a"} <code>review_item_id</code>{ja ? " が含まれます。" : "."}</li>
        <li><strong>{ja ? "ブロック" : "Block"}</strong>{" — "}{ja ? "403で拒否。LLM呼び出しは行われません。" : "rejected with a 403. No LLM call is made."}</li>
      </ul>

      <h2 id="hitl">Human-in-the-Loop (HitL)</h2>
      <p>
        {ja
          ? "キューに入ったリクエストはダッシュボードの"
          : "Queued requests appear in the"}{" "}
        <strong>{ja ? "レビューキュー" : "Review Queue"}</strong>{" "}
        {ja ? "に表示されます。レビュー担当者は3つのアクションを実行できます：" : "in the dashboard. Reviewers can take three actions:"}
      </p>
      <ul>
        <li><strong>{ja ? "承認" : "Approve"}</strong>{" — "}{ja ? "リクエストをLLMに転送し、レスポンスを返します。" : "the request is forwarded to the LLM and the response returned."}</li>
        <li><strong>{ja ? "却下" : "Reject"}</strong>{" — "}{ja ? "リクエストを403で拒否します。" : "the request is rejected with a 403."}</li>
        <li><strong>{ja ? "エスカレーション" : "Escalate"}</strong>{" — "}{ja ? "アクションを取らず、上位レビュー担当者にフラグを立てます。" : "the item is flagged for senior review without taking action."}</li>
      </ul>

      <h3 id="sla">{ja ? "SLA・フォールバック" : "SLA & Fallback"}</h3>
      <p>
        {ja
          ? "各レビューアイテムにはSLA期限があります（デフォルト：30分、ポリシーごとに設定可能）。バックグラウンドワーカーが60秒ごとに期限切れアイテムをチェックし、設定された"
          : "Each review item has an SLA deadline (default: 30 minutes, configurable per policy). A background worker polls every 60 seconds for expired items and applies the configured"}{" "}
        <strong>{ja ? "SLAフォールバックアクション" : "SLA fallback action"}</strong>{ja ? "を適用します：" : ":"}
      </p>
      <ul>
        <li><code>block</code>{ja ? "（デフォルト）— 期限切れアイテムを自動ブロック" : " (default) — expired items are auto-blocked"}</li>
        <li><code>allow</code>{" — "}{ja ? "期限切れアイテムを自動承認して転送" : "expired items are auto-approved and forwarded"}</li>
      </ul>

      <h2 id="capabilities">{ja ? "Capability-Based Access Control（Layer 4）" : "Capability-Based Access Control (Layer 4)"}</h2>
      <p>
        {ja
          ? "v1.3.0で追加。Google DeepMind CaMeL論文に基づき、制御フローとデータフローを分離します。Capabilityトークンは暗号ノンスで生成され、注入テキストからは偽造できません。UNTRUSTED（信頼できない）データはスキャンなしにTRUSTEDに昇格できないため、データ→制御フローのエスカレーション攻撃を防ぎます。"
          : "Added in v1.3.0. Based on Google DeepMind's CaMeL paper, this layer separates control flow from data flow. Capability tokens are generated with cryptographic nonces — unforgeable by injected text. UNTRUSTED data cannot be promoted to TRUSTED without scanning, preventing data-to-control-flow escalation attacks."}
      </p>
      <ul>
        <li><code>Capability</code>{" — "}{ja ? "暗号ノンス付きのアクセス許可トークン。スコープ・有効期限を持つ" : "access permission token with cryptographic nonce, scope, and expiry"}</li>
        <li><code>TaintLabel</code>{" — "}TRUSTED / UNTRUSTED / SANITIZED{ja ? " のデータ出自分類" : " data provenance classification"}</li>
        <li><code>CapabilityEnforcer</code>{" — "}{ja ? "UNTRUSTED状態でshell:exec, agent:spawn, code:evalなどの制御フロー操作をブロック" : "blocks control-flow operations (shell:exec, agent:spawn, code:eval) when data provenance is UNTRUSTED"}</li>
        <li><code>Guard.authorize_tool()</code>{" — "}{ja ? "メインAPIにケーパビリティ検証を統合する新メソッド" : "new method integrating capability checks into the main API"}</li>
      </ul>

      <h2 id="aep">{ja ? "Atomic Execution Pipeline — AEP（Layer 5）" : "Atomic Execution Pipeline — AEP (Layer 5)"}</h2>
      <p>
        {ja
          ? "v1.3.0で追加。ツール実行を「スキャン → 実行 → 蒸発」の不可分な単一操作として定義します。入力は常にスキャン済み、実行は常にサンドボックス内、成果物は常に破壊（明示的オプトアウト時は監査警告付き）。"
          : "Added in v1.3.0. Defines tool execution as an indivisible primitive: Scan, Execute, Vaporize. Input is always scanned, execution is always sandboxed, artifacts are always destroyed (with audit warning if explicitly opted out)."}
      </p>
      <ul>
        <li><code>ProcessSandbox</code>{" — "}{ja ? "stdlib-onlyの実行サンドボックス（subprocess + tempdir、環境変数除去、タイムアウト制御）" : "stdlib-only execution sandbox (subprocess + tempdir, environment stripping, timeout enforcement)"}</li>
        <li><code>Vaporizer</code>{" — "}{ja ? "os.urandomで上書き後にunlink、検証パスで確実に破壊" : "secure artifact destruction with os.urandom overwrite before unlink, verification pass"}</li>
        <li><code>AtomicPipeline</code>{" — "}{ja ? "スレッドセーフなオーケストレータ。3ステップの不可分性を保証" : "thread-safe orchestrator guaranteeing indivisibility of the 3-step sequence"}</li>
      </ul>

      <h2 id="safety-verifier">{ja ? "Safety Verifier（Layer 6）" : "Safety Verifier (Layer 6)"}</h2>
      <p>
        {ja
          ? "v1.3.0で追加。宣言的な安全仕様（SafetySpec）を定義し、実行前に検証します。検証に合格するとProofCertificate（UUID4 + UTCタイムスタンプ）が発行され、監査証跡として使用できます。"
          : "Added in v1.3.0. Define declarative safety specifications (SafetySpec) and verify them before execution. On passing verification, a ProofCertificate (UUID4 + UTC timestamp) is issued for audit trails."}
      </p>
      <ul>
        <li><code>SafetySpec</code>{" — "}<code>allowed_effects</code>{", "}<code>forbidden_effects</code>{", "}<code>invariants</code>{ja ? " を宣言" : ""}</li>
        <li><code>SafetyVerifier</code>{" — "}{ja ? "組み込み不変条件チェック：" : "built-in invariant checks: "}<code>check_no_secrets_in_output</code>{", "}<code>check_no_pii_in_output</code>{", "}<code>check_path_traversal</code></li>
        <li><code>DEFAULT_SAFETY_SPEC</code>{" — "}{ja ? "8許可・10禁止・2不変条件" : "8 allowed, 10 forbidden, 2 invariants"}</li>
        <li><code>STRICT_SAFETY_SPEC</code>{" — "}{ja ? "より厳格な安全仕様" : "stricter safety specification"}</li>
      </ul>

      <h2 id="policy-engine">{ja ? "ポリシーエンジン" : "Policy Engine"}</h2>
      <p>
        {ja
          ? "各テナントには、ルーティング動作を制御するアクティブな"
          : "Each tenant has one active"}{" "}
        <strong>{ja ? "ポリシー" : "Policy"}</strong>{ja ? "があります：" : " that controls routing behavior:"}
      </p>
      <ul>
        <li><code>auto_allow_threshold</code>{" — "}{ja ? "この値以下のスコアは自動許可（デフォルト：30）" : "scores ≤ this value are auto-allowed (default: 30)"}</li>
        <li><code>auto_block_threshold</code>{" — "}{ja ? "この値以上のスコアは自動ブロック（デフォルト：81）" : "scores ≥ this value are auto-blocked (default: 81)"}</li>
        <li><code>review_sla_minutes</code>{" — "}{ja ? "人間レビューのSLA時間（デフォルト：30）" : "SLA time for human review (default: 30)"}</li>
        <li><code>sla_fallback</code>{" — "}<code>&quot;block&quot;</code>{ja ? " または " : " or "}<code>&quot;allow&quot;</code></li>
        <li><code>custom_rules</code>{" — "}{ja ? "カスタムスコアデルタ付きの追加正規表現パターンの配列" : "array of additional regex patterns with custom score deltas"}</li>
      </ul>

      <h2 id="multi-tenancy">{ja ? "マルチテナンシー" : "Multi-Tenancy"}</h2>
      <p>
        {ja
          ? "Aigis は完全なマルチテナント対応です。各テナントはデータが分離されています：独自のポリシー・ユーザー・レビューキュー・監査ログ。テナントIDはプロキシリクエストの認証に使用するAPIキーによって決定されます。ダッシュボードアクセスにはJWTトークンを使用します。"
          : "Aigis is fully multi-tenant. Each tenant has isolated data: their own policies, users, review queues, and audit logs. Tenant identity is determined by the API key used to authenticate proxy requests. JWT tokens are used for dashboard access."}
      </p>
    </DocsLayout>
  );
}
