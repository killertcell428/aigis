---
title: Microsoftが9パッケージで解決しようとしていることを、pip install 1行で始める
tags:
  - AIエージェント
  - セキュリティ
  - Python
  - Microsoft
  - LLM
private: false
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: false
---

## TL;DR

2026年4月2日、MicrosoftがAIエージェントのランタイムセキュリティに特化したOSSツールキット「**Agent Governance Toolkit**」を公開した。9パッケージ構成、5言語SDK、OWASP Agentic AI Top 10の全項目をカバーする大規模プロジェクトだ。

これは**市場の正当化**だ。

「AIエージェントにセキュリティは必要か？」という問いは終わった。Microsoftが200+ページのドキュメントと9,500テストを投入して「必要だ」と言っている。

本記事では、この巨大ツールキットと、筆者が開発するOSSファイアウォール「**Aigis**」を比較し、**どちらをどの場面で選ぶべきか**を整理する。

---

## Microsoftが来た — 何が変わるのか

### Agent Governance Toolkitとは

MicrosoftがApache 2.0ライセンスで公開した、AIエージェント向けのランタイムセキュリティフレームワーク。設計思想は3つの既存ドメインから借用している。

| 借用元 | 適用 |
|--------|------|
| **OSカーネル** | 特権リング（Ring 0〜3）、ケーパビリティベースのアクセス制御 |
| **サービスメッシュ** | DIDベースのゼロトラスト認証、相互TLS |
| **SRE** | SLO/エラーバジェット、サーキットブレーカー、カオスエンジニアリング |

### 9パッケージの全体像

```
Agent Governance Toolkit
├── Agent OS          … ポリシーエンジン（YAML/OPA Rego/Cedar対応）
├── Agent Mesh        … ゼロトラストID + 信頼スコア（0-1000）
├── Agent Runtime     … CPU風特権リング（Ring 0-3）+ サーガオーケストレーション
├── Agent SRE         … SLO監視 + カオスエンジニアリング（9テンプレート）
├── Agent Compliance  … OWASP検証 + 規制マッピング
├── Agent Discovery   … シャドーAI検出
├── Agent Hypervisor  … 実行計画の事前検証 + 可逆性チェック
├── Agent Marketplace … プラグインライフサイクル管理（Ed25519署名）
└── Agent Lightning   … RL訓練ガバナンス
```

控えめに言って、**エンタープライズのためのフルスタック**だ。

---

## 比較: Microsoft vs Aigis

### 設計思想の違い

まず明確にしておきたいのは、**両者は競合ではなく、異なるユースケースに対する解**だということだ。

| | **Microsoft Agent Governance Toolkit** | **Aigis** |
|---|---|---|
| **一言で言うと** | エンタープライズ向けフルスタックガバナンス基盤 | 開発者のための軽量セキュリティファイアウォール |
| **設計思想** | OSカーネル + サービスメッシュ + SRE | ファイアウォール（4層防御 → 6層に拡張中） |
| **ターゲット** | プラットフォームチーム、SRE、CISO | 個人開発者 → スタートアップ → 中小企業 |

### インストールと導入

```bash
# Microsoft — フルインストール
pip install agent-governance-toolkit[full]
# + YAML/Regoでポリシー定義 + DID設定 + 信頼スコア閾値設定...

# Aigis — 3行で完了
pip install pyaigis
```

```python
# Aigis: 文字通り3行
from aigis import Guard
guard = Guard()
result = guard.check_input("Ignore all previous instructions")
# → blocked=True, risk_level=CRITICAL
```

**Microsoftのツールキットは「導入」ではなく「構築」を求める。** ポリシーファイルの設計、信頼スコアの閾値調整、特権リングの割り当て — これらは正しいアプローチだが、専任のプラットフォームチームが前提になる。

Aigisは**インストールした瞬間に防御が始まる**。デフォルトで165+のパターン、44のコンプライアンステンプレートが有効化される。設定ゼロ。

### 機能比較

| 機能 | Microsoft | Aigis |
|------|-----------|-------|
| **プロンプトインジェクション検出** | ポリシーベース（ユーザー定義） | 165+パターン内蔵（日英中韓） |
| **MCP/ツールセキュリティ** | MCP Security Gateway | MCPツールスキャナー + 信頼スコア + Rug Pull検出 |
| **コンプライアンス** | EU AI Act, HIPAA, SOC2 | US/EU/中国/日本 44テンプレート |
| **日本語対応** | なし（英語のみ） | ネイティブ（21パターン + APPI/マイナンバー法） |
| **多言語パターン** | なし | 英語 + 日本語 + 韓国語 + 中国語 |
| **特権リング** | Ring 0-3（CPU風） | CaMeL inspired ケーパビリティ制御 |
| **サーキットブレーカー** | あり（Agent SRE） | なし |
| **カオスエンジニアリング** | 9テンプレート | 自己攻撃ループ（Adversarial Loop） |
| **SDK言語** | Python, TS, .NET, Rust, Go | Python |
| **外部依存** | 複数パッケージ | **ゼロ**（Python標準ライブラリのみ） |
| **レイテンシ** | <0.1ms（ポリシー評価） | ~50μs（正規表現ベース） |
| **テスト数** | 9,500+ | 901 |
| **ライセンス** | MIT | Apache 2.0 |

### OWASP Agentic AI Top 10 対応状況

| # | リスク | Microsoft | Aigis |
|---|--------|-----------|-------|
| 1 | Agentic Prompt Injection | Policy Engine | 4層検出 + デコード |
| 2 | Tool Misuse | Ring 0-3 制御 | MCPスキャナー + 信頼スコア |
| 3 | Excessive Permissions | ケーパビリティゲーティング | CaMeL ケーパビリティ制御 |
| 4 | Insufficient Sandboxing | Agent Hypervisor | AEP（Atomic Execution Pipeline） |
| 5 | Insecure Output | ポリシールール | 出力スキャン（PII/SQLi/XSS） |
| 6 | Lack of Oversight | Agent SRE + SLO | 監査ログ + コンプライアンス |
| 7 | Unsafe Inter-Agent | Agent Mesh (DID) | 多エージェント監視 |
| 8 | Supply Chain Attacks | Marketplace署名 | SHA-256ハッシュピンニング + SBOM |
| 9 | Data Leakage | ポリシーベース | PII検出（11+パターン、日本固有含む） |
| 10 | Insufficient Logging | OpenTelemetry連携 | 構造化監査ログ |

---

## どちらを選ぶべきか

### Microsoft Agent Governance Toolkitを選ぶ場面

- **50人以上のエンジニアチーム**がマルチエージェントシステムを運用している
- **Azure上にデプロイ**しており、既存インフラとの統合が前提
- **専任のプラットフォームチーム/SREチーム**がいる
- **複数言語のSDK**（Python + TypeScript + .NET）が必要
- カオスエンジニアリング、サーキットブレーカーなど**SRE的なガバナンス**が求められる

### Aigisを選ぶ場面

- **今すぐ防御を始めたい**（設定不要、pip installから30秒）
- **日本語環境**でAIエージェントを運用している
- **個人/小規模チーム**で、専任のセキュリティチームがいない
- **依存関係ゼロ**を重視する（サプライチェーンリスクの最小化）
- Claude Code、LangChain、OpenAI SDKなどの**既存ワークフローに素早く統合**したい
- **日本の法規制**（AI事業者ガイドラインv1.2、総務省セキュリティGL、APPI）への対応が必要

### 両方使う場面

実は、**排他的な選択ではない**。

```python
# Aigisをファーストレイヤーとして使い、
# Microsoft Toolkitをガバナンス基盤として使う

from aigis import Guard
from agent_os.policies import PolicyEvaluator

# Step 1: Aigisで高速パターンマッチング（~50μs）
guard = Guard()
result = guard.check_input(user_input)
if result.blocked:
    return block_response(result)

# Step 2: Microsoft Toolkitでポリシー評価
evaluator = PolicyEvaluator()
policy_result = evaluator.evaluate(action_context)
if not policy_result.allowed:
    return deny_response(policy_result)

# Step 3: エージェント実行
agent.run(user_input)
```

Aigisの正規表現ベースの高速検出を**第一防御壁**として配置し、Microsoftのポリシーエンジンを**ガバナンス層**として重ねる。レイテンシへの影響はほぼゼロだ。

---

## 巨人の参入が意味すること

Microsoftの参入は、3つのことを証明している。

**1. 市場は本物だ**

「AIエージェントセキュリティ」は一時的なバズワードではない。Microsoftが9パッケージ、5言語SDK、9,500テストを投入するのは、**この問題が解決に値する**と判断したからだ。

**2. エンタープライズ向けだけでは足りない**

Microsoftのアプローチは正しいが、すべての開発者がRing 0-3やDIDやサーガオーケストレーションを必要としているわけではない。**「まず守る、次に整える」** というボトムアップのアプローチにも居場所がある。

**3. OSSが勝つ**

両者ともオープンソースだ。プロプライエタリな$50,000/年のソリューションは、もはや正当化が難しくなった。

---

## まとめ

| あなたの状況 | 推奨 |
|---|---|
| 「とにかく今すぐ守りたい」 | `pip install pyaigis` |
| 「日本語環境で使いたい」 | Aigis（日本語ネイティブ対応） |
| 「エンタープライズガバナンス基盤を構築したい」 | Microsoft Agent Governance Toolkit |
| 「Azure上でマルチエージェントを運用中」 | Microsoft Agent Governance Toolkit |
| 「両方の良いとこ取りをしたい」 | Aigis（検出層）+ Microsoft（ガバナンス層） |

Microsoftの参入により、AIエージェントセキュリティは**ニッチからメインストリーム**に移行した。

問題は「セキュリティは必要か？」ではなく、「**どこから始めるか？**」になった。

その答えの一つが、`pip install pyaigis` だ。

---

**Aigis** — The open-source firewall for AI agents.
GitHub: [killertcell428/aigis](https://github.com/killertcell428/aigis)
PyPI: [pyaigis](https://pypi.org/project/pyaigis/)
