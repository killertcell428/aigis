---
title: "AIエージェントの暴走は「モデルの問題」ではなく「権限の問題」——2026年Q1のインシデントから考えるエージェントセキュリティ設計"
emoji: "🔐"
type: "tech"
topics: ["AIエージェント", "セキュリティ", "LLM", "ゼロトラスト", "ClaudeCode"]
published: true
---

## はじめに——エージェントは「答える」のではなく「行動する」

2026年Q1、AIエージェントのセキュリティインシデントが立て続けに報告されました。

- **Meta**: 内部AIエージェントが暴走し、未承認の社員に機密データを公開（3月）
- **PleaseFix脆弱性**: エージェンティックブラウザPerplexity Cometで、ゼロクリックでローカルファイルにアクセスできる脆弱性が発覚（3月）
- **McKinsey**: レッドチーム演習で、内部AIプラットフォーム「Lilli」が2時間以内にシステム全体のアクセス権を取得（非公開→Bessemer VPレポートで言及）

これらのインシデントに共通する教訓があります。Bessemer Venture Partnersのレポートが端的に表現しています：

> **「Most agentic failures are not model failures but authority failures — the agent was permitted to do something it should never have been allowed to do.」**
> （エージェントの失敗の大半はモデルの問題ではなく権限の問題——エージェントは、本来許可されるべきでないことを許可されていた。）

この記事では、2026年Q1のインシデントを技術的に分析し、エージェントセキュリティを「権限設計」の観点から体系的に考えます。

## 1. Metaの暴走エージェント——何が起きたのか

### インシデント概要

TechCrunch（3月18日）の報道によると、Metaの内部AIエージェントが適切な承認なしにレスポンスを返し、大量の機密データが未承認の社員にアクセス可能になりました。

### 技術的な問題

根本原因は**エージェントの権限委譲モデルの不備**です。従来のアプリケーションでは、ユーザーの権限はセッション単位で管理されます。しかしエージェントは、ユーザーの代理として行動する際に、**元のユーザーの権限範囲を超えたアクションを実行できてしまう**設計でした。

```
従来のモデル:
  ユーザーA(権限: 部門データのみ) → API → 部門データを返す ✅

エージェントモデル（問題あり）:
  ユーザーA → エージェント(権限: システム全体) → 全社データを返す ❌
                 ↑ エージェント自体の権限が過剰
```

これは「Confused Deputy Problem」（混乱した代理問題）の典型例です。エージェントはユーザーAの代理として動いているのに、エージェント自体のサービスアカウント権限で全データにアクセスできてしまう。

### Ciscoの調査が裏付ける現実

Ciscoの「State of AI Security 2026」によると：
- エージェント型AIの導入を計画している組織は多いが、セキュリティ対策が準備できていると回答したのは**わずか29%**
- **半数以上のエージェントが、セキュリティレビューなしで本番環境にデプロイ**されている
- エージェントが接続するツールやAPIを、セキュリティチームがマッピングしていないケースが多数

## 2. PleaseFix——エージェンティックブラウザのゼロクリック攻撃

### エージェンティックブラウザとは

Perplexity Cometに代表される「エージェンティックブラウザ」は、従来のブラウザとは異なり、**指示を解釈し、認証コンテキストを保持し、アプリケーション間で自律的にアクションを実行する**能力を持ちます。

つまり、ブラウザそのものがAIエージェントとして振る舞う。

### 2つの攻撃パス

Zenity Labsが発見した「PleaseFix」は、2つの異なる攻撃パスを持つ脆弱性です。

**攻撃パス1: ゼロクリック型データ窃取**

```
攻撃者 → カレンダー招待にペイロードを埋め込む
          ↓
ユーザーのエージェンティックブラウザがカレンダーを開く
          ↓
エージェントがペイロードを解釈（プロンプトインジェクション）
          ↓
ローカルファイルシステムにアクセス → データ窃取
          ↓
ユーザーには正常な応答を表示（気づかない）
```

ポイントは**ユーザーの操作が一切不要**なこと。カレンダーの定期読み込みだけでトリガーされます。

**攻撃パス2: パスワードマネージャー連携の悪用**

エージェントがパスワードマネージャーと連携している場合、エージェントの権限を引き継いで認証情報を窃取、またはアカウント乗っ取りが可能。

### なぜ従来のブラウザセキュリティでは防げないのか

従来のブラウザセキュリティ（Same-Origin Policy、CSP等）は**ページ単位**でリソースを隔離します。しかしエージェンティックブラウザは設計上、**複数のページ・アプリケーションをまたいで行動する**ため、従来の隔離モデルが機能しません。

## 3. OWASP Agentic Top 10 が示すリスク構造

OWASPが2025年末に公開した「Agentic Applications Top 10 2026」は、こうしたインシデントを体系的に整理しています。

特にQ1のインシデントと直結するリスクは以下の3つです：

| ID | リスク | Q1インシデントとの関連 |
|---|---|---|
| ASI01 | Excessive Agency | Metaの暴走エージェント——エージェントの権限が過剰 |
| ASI03 | Insecure Credential Management | PleaseFix——パスワードマネージャー連携の悪用 |
| ASI05 | Indirect Prompt Injection | PleaseFix——カレンダー経由のゼロクリック攻撃 |

ここで重要なのは、**これらのリスクはモデルの性能とは無関係**だということ。GPT-5でもClaude 4でも、権限設計が不適切なら同じインシデントが起きます。

## 4. エージェントセキュリティ設計の原則

Q1のインシデントから導き出される設計原則を整理します。

### 原則1: 最小権限の原則（Principle of Least Privilege）

エージェントには、タスクの実行に**必要最小限の権限**のみを付与する。

```yaml
# ❌ 悪い例: エージェントに広範な権限を付与
agent:
  permissions:
    - read: "/**"
    - write: "/**"
    - execute: "/**"

# ✅ 良い例: タスクごとに権限を限定
agent:
  role: "code-review"
  permissions:
    - read: "/src/**"
    - read: "/tests/**"
    # write権限なし、.env等へのアクセスなし
  denied:
    - read: "/.env*"
    - read: "/**/*.key"
    - execute: "curl|wget|nc"
```

### 原則2: 権限の委譲を明示的にする

エージェントがユーザーの代理として動く場合、**ユーザーの権限を超えないことをシステム的に保証**する。

```python
class AgentAuthorizationProxy:
    """エージェントの権限をユーザーの権限範囲に制限する"""

    def __init__(self, user_context, agent_context):
        self.user_permissions = user_context.permissions
        self.agent_permissions = agent_context.permissions

    def can_access(self, resource):
        # ユーザーとエージェント両方の権限を満たす場合のみ許可
        return (
            self.user_permissions.allows(resource)
            and self.agent_permissions.allows(resource)
        )

    def execute(self, action):
        if not self.can_access(action.target_resource):
            raise AuthorizationError(
                f"Agent denied: user lacks permission for {action.target_resource}"
            )
        return action.run()
```

### 原則3: エージェントの入出力を監視する

エージェントが処理するすべての入力と出力に対して、セキュリティスキャンを実施する。

```python
from aig_guardian import Guardian

guardian = Guardian()

# エージェントへの入力（外部コンテンツ含む）をスキャン
def process_agent_input(content: str) -> str:
    result = guardian.scan_input(content)
    if result.risk_score >= 80:
        raise SecurityError(f"High risk input blocked: {result.threats}")
    if result.risk_score >= 50:
        log_warning(f"Suspicious input detected: {result.threats}")
    return content

# エージェントの出力をスキャン（PII・クレデンシャル漏洩防止）
def process_agent_output(output: str) -> str:
    result = guardian.scan_output(output)
    if result.has_pii:
        output = result.redacted  # PIIをマスク
        log_alert(f"PII detected and redacted: {result.pii_types}")
    return output
```

**Aigis**は64種類の検出パターンでプロンプトインジェクション・PII漏洩・データ窃取を検出するOSSライブラリです。日本語攻撃パターンにも対応しており、3行で既存のアプリケーションに統合できます。

> GitHub: https://github.com/killertcell428/aigis
> PyPI: `pip install aigis`

### 原則4: ゼロトラストをエージェントに適用する

OpenID Foundationが「Identity Management for Agentic AI」で指摘しているように、現行のアイデンティティフレームワークはエージェントのシナリオでは機能しません。

エージェントに対してもゼロトラストの考え方を適用する必要があります：

```
従来のゼロトラスト:         エージェント時代のゼロトラスト:
  Never trust, always verify     Never trust, always verify
  ユーザー → リソース            ユーザー → エージェント → リソース
                                      ↑ ここも検証が必要
```

具体的には：
- **エージェントの身元確認**: どのエージェントがどのモデルで動いているか
- **アクションごとの承認**: 高リスクな操作（ファイル削除、外部API呼び出し）には人間の承認を要求
- **セッション管理**: エージェントのセッションにTTL（有効期限）を設定
- **監査ログ**: 全アクションを記録し、異常検知を実施

## 5. 情シスが明日からやるべきこと

技術的な原則を理解した上で、組織としてのアクションプランを整理します。

### フェーズ1: 可視化（1週間）

```
□ 社内で使われているAIエージェントを棚卸し
□ 各エージェントがアクセスできるリソースをマッピング
□ セキュリティレビューなしでデプロイされたエージェントを特定
```

### フェーズ2: ガードレール設置（1ヶ月）

```
□ エージェントの権限ポリシーを策定
□ 高リスク操作の承認フローを設計
□ 入出力の監視・ログ体制を構築
□ インシデント対応手順を文書化
```

### フェーズ3: 継続的改善（四半期ごと）

```
□ 権限ポリシーの見直し
□ レッドチーム演習の実施
□ 新しいCVE・攻撃手法のキャッチアップ
□ エージェントセキュリティのKPI測定
```

## まとめ

2026年Q1のインシデントが繰り返し示しているメッセージは明確です：

**エージェントの問題は「AIが賢いかどうか」ではなく「何を許可するか」で決まる。**

モデルの性能向上は攻撃の影響範囲も拡大させます。だからこそ、権限設計・入出力監視・ゼロトラストの原則がこれまで以上に重要になっています。

AIエージェントは確実に業務を変革します。その変革を安全に享受するために、セキュリティを「後付け」ではなく「設計の一部」として組み込んでいきましょう。

## 参考リンク

- [Securing AI agents: the defining cybersecurity challenge of 2026 - Bessemer VP](https://www.bvp.com/atlas/securing-ai-agents-the-defining-cybersecurity-challenge-of-2026)
- [Meta is having trouble with rogue AI agents - TechCrunch](https://techcrunch.com/2026/03/18/meta-is-having-trouble-with-rogue-ai-agents/)
- [PleaseFix: Agentic Browser Vulnerability - Help Net Security](https://www.helpnetsecurity.com/2026/03/04/agentic-browser-vulnerability-perplexedbrowser/)
- [Cisco State of AI Security 2026](https://blogs.cisco.com/ai/cisco-state-of-ai-security-2026-report)
- [AI Agent Security Risks in 2026 - Practitioner's Guide](https://blog.cyberdesserts.com/ai-agent-security-risks/)
- [OWASP Agentic Applications Top 10](https://owasp.org/www-project-agentic-applications-top-10/)
- [Aigis - LLMセキュリティライブラリ](https://github.com/killertcell428/aigis)

---

:::message
📚 **この記事の内容をさらに深く学ぶなら**
本記事のテーマは、Zenn本 **[AIエージェント・セキュリティ＆ガバナンス実践ガイド](https://zenn.dev/sharu389no/books/ai-agent-security-governance)** で体系的に解説しています。OWASP Agentic Top 10、MCPセキュリティ、NHI管理、EU AI Act対応まで、全18章で網羅。
:::
