# 本の再構成計画：AIエージェント・セキュリティ＆ガバナンス実践ガイド

## 現状の課題

- 記事ベースの寄せ集めで、体系的な技術書になっていない
- 「何を学べば網羅できるか」が構造化されていない
- aigisの紹介が自然に組み込まれていない

## 目指す姿

**AIエージェントを統制するための手引き書・完全版の取り扱い書**
- セキュリティとガバナンスに焦点
- 基礎から順に読めば体系的に理解できる構成
- aigisは対応可能な技術領域で自然に紹介（裏KPI）
- 対応できない領域はベストなツールを公平に提案

---

## 新構成案（5部構成）

### 第I部：基礎知識編 — AIエージェントセキュリティの地図を手に入れる

> 読者が「何を守るべきか」「何が危険か」の全体像を掴む

#### 第1章：AIエージェントとは何か — セキュリティの視点から
- 1.1 エージェントの定義と分類（単一/マルチ、リアクティブ/自律型）
- 1.2 従来AIとの決定的な違い：**ツールを使い、外部に作用する**
- 1.3 エージェントのライフサイクル（計画→推論→行動→評価）
- 1.4 セキュリティ視点の攻撃面マッピング：プロンプト層・ツール層・メモリ層・通信層
- 📰 コラム：「Lethal Trifecta」— なぜエージェントは危険なのか

#### 第2章：脅威の全体像 — OWASP Agentic Top 10 を読み解く
- 2.1 OWASP Agentic Top 10（2026年版）の10リスク概説
  - ASI01 Agent Goal Hijack ～ ASI10 Rogue Agents
- 2.2 各リスクの関連性マップ（連鎖的に発生するパターン）
- 2.3 自社に当てはまるリスクの見つけ方（簡易アセスメント）
- 📰 コラム：MITRE ATLAS — AIに特化した攻撃戦術フレームワーク

#### 第3章：知っておくべきフレームワークと規制
- 3.1 NIST AI Risk Management Framework（AI RMF）— 4機能の概要
- 3.2 ISO/IEC 42001 — AI管理システムの国際標準
- 3.3 EU AI Act — エージェントに関わる規定と施行スケジュール
- 3.4 シンガポール Model AI Governance Framework for Agentic AI
- 3.5 日本の規制動向
  - AI事業者ガイドライン v1.2（エージェント初対応）
  - 総務省AIセキュリティガイドライン
  - デジタル庁 生成AI調達ガイドライン
- 3.6 フレームワーク対応マトリクス（OWASP × NIST × ISO × EU × JP）
- 📰 コラム：規制タイムライン 2025-2027

---

### 第II部：応用編 — 技術で守る：攻撃と防御の実際

> 各脅威領域の技術的な深掘り。攻撃手法→防御設計→実装パターンの流れ

#### 第4章：プロンプトインジェクション — 最も身近で最も厄介な脅威
- 4.1 攻撃の分類：直接 vs 間接プロンプトインジェクション
- 4.2 実際の攻撃手法と事例
  - マルチステップ攻撃チェーン
  - MemoryGraft攻撃（偽成功体験のメモリ植え付け）
- 4.3 防御技術
  - Defense-in-Depth（PALADIN 5層防御）
  - Sentinel Architecture（監視エージェント方式）
  - XML タギング・権限分離プロンプト
  - LLM-as-Critic 出力検証層
- 4.4 構造的限界：なぜ完全防御は不可能なのか
- 🛡️ **ツール紹介**：
  - **Aigis** — 正規表現+類似度ベースの入出力スキャン（64パターン、日本語対応）
  - Rebuff / LLM Guard / Prompt Armor — LLMベースの検出
  - OpenAI Moderation API / Azure Content Safety

#### 第5章：MCPセキュリティ — ツール連携の信頼境界
- 5.1 MCPアーキテクチャとセキュリティモデル
- 5.2 攻撃パターン
  - ツールポイズニング（description injection）
  - Rug Pull攻撃（サーバー更新による権限昇格）
  - Echo Leak（PII流出）
- 5.3 MCP信頼境界の設計
  - OAuth Resource Indicators（RFC 8707）必須化
  - サーバーサンドボックス化（コンテナ/gVisor/Kata）
  - ツール呼び出しの入力検証・サニタイズ
- 5.4 MCPサーバーの選定基準とサプライチェーンリスク
- 🛡️ **ツール紹介**：
  - **Aigis** — MCPツール呼び出しの事前スキャン（Claude Code hook統合）
  - Invariant Labs MCP Scanner
  - CoSAI MCP Security Guide（設計ガイドライン）

#### 第6章：エージェントID・認証・認可 — Non-Human Identityの管理
- 6.1 NHI爆発の現実：人間の25-50倍、2026年末450億超
- 6.2 NHIライフサイクル管理（発行・ローテーション・失効）
- 6.3 技術スタック
  - SPIFFE/SPIRE によるワークロードID
  - OAuth 2.0 Client Credentials + スコープ制限
  - Workload Identity Federation（クラウド）
- 6.4 ゼロトラストのエージェント適用
  - Microsoft ZT4AI リファレンスアーキテクチャ
  - CSA Agentic Trust Framework
  - ゼロスタンディング特権（ZSP）
- 🛡️ **ツール紹介**：
  - HashiCorp Vault（SPIFFE認証ネイティブ）
  - CyberArk / Astrix / Clutch Security（NHI管理プラットフォーム）
  - **Aigis** — ポリシーエンジンによるアクセス制御（YAML定義）

#### 第7章：マルチエージェント通信のセキュリティ
- 7.1 A2Aプロトコルの仕組みとセキュリティモデル
- 7.2 MCP vs A2A：役割の違いと組み合わせ方
- 7.3 脅威と対策
  - エージェント間メッセージスプーフィング
  - 権限の連鎖的委任リスク
  - 共有NHIの再利用による連鎖障害（ASI08）
- 7.4 信頼境界の設計パターン
- 🛡️ **ツール紹介**：
  - Microsoft Agent Governance Toolkit（Ed25519暗号ID + SPIFFE）
  - A2A公式セキュリティガイド

#### 第8章：コード実行とサンドボックス
- 8.1 動的生成コードのリスク（Python/Bash/SQL）
- 8.2 実行隔離技術の比較
  - コンテナ（Docker/Podman）
  - マイクロVM（Firecracker/Kata）
  - gVisor / WebAssembly
- 8.3 リソース制御とブラストラディウス限定
- 8.4 コーディングエージェント（Claude Code/Cursor）のセキュリティ設計
- 🛡️ **ツール紹介**：
  - **Aigis** — Claude Code PreToolUse hookによるコマンド実行前スキャン
  - E2B / Modal / Fireworks（クラウドサンドボックス）
  - Claude Code自体のパーミッションモデル

---

### 第III部：実践編 — 組織に導入する

> 技術を組織のガバナンスに落とし込む。チーム体制・ポリシー・運用設計

#### 第9章：ガバナンス体制の構築
- 9.1 エージェントガバナンスの成熟度モデル（現状：成熟企業は約20%）
- 9.2 AI CoE（Center of Excellence）の設置と役割
- 9.3 RACIマトリクス：開発・セキュリティ・法務・経営の責任分担
- 9.4 ポリシー as Code：GitOpsで管理する行動規範
  - OPA / Cedar のエージェント適用
  - 決定論的ポリシー評価（サブミリ秒）
- 🛡️ **ツール紹介**：
  - **Aigis** — YAMLポリシーエンジン（14ルール組込み、業種別テンプレート7種）
  - OPA（Open Policy Agent）/ AWS Cedar

#### 第10章：Human-in-the-Loop の設計
- 10.1 3つの基本パターン
  - Approval Gate / Escalation Trigger / Tiered Escalation
- 10.2 制度的要件（EU AI Act第14条 / NIST AI RMF）
- 10.3 実装アーキテクチャ
  - ワークフローエンジン統合（Temporal/Airflow）
  - Slack/Teams承認フロー
  - 監査証跡の自動生成
- 10.4 「ラバースタンプ」問題への対処（ASI09）

#### 第11章：監査・オブザーバビリティ
- 11.1 エージェントオブザーバビリティの5要素
  - 推論トレース / ツール呼び出しログ / データアクセス / メトリクス / ガードレール違反
- 11.2 OpenTelemetry GenAI セマンティック規約
- 11.3 コンプライアンスレポートの自動生成
- 🛡️ **ツール紹介**：
  - **Aigis** — 3層アクティビティストリーム + CSVエクスポート + コンプライアンスレポート（24規制要件マッピング）
  - LangSmith / LangFuse / Helicone（SaaS型）
  - Datadog / Dynatrace（エンタープライズ統合）

#### 第12章：レッドチーミングと継続的テスト
- 12.1 エージェント専用レッドチーミング手法
  - NIST実証：攻撃成功率81%（ベースライン防御比11%）
- 12.2 自動化レッドチーミング
  - 強化学習ベースの攻撃生成
  - DeepTeam / Confident AI
- 12.3 CI/CD統合による継続的セキュリティテスト
- 12.4 規制要件としてのレッドチーミング（EU AI Act 2026年8月完全施行）
- 🛡️ **ツール紹介**：
  - **Aigis** — `aig benchmark`（検出精度テスト）
  - Garak / DeepTeam / Promptfoo（攻撃生成）
  - Azure AI Red Teaming

#### 第13章：エンタープライズ導入ロードマップ
- 13.1 Phase 1: 現状評価（30日）— リスクアセスメントと優先順位付け
- 13.2 Phase 2: 基盤構築（60日）— ポリシー定義・ツール導入・チーム教育
- 13.3 Phase 3: 運用開始（90日）— 監視・改善サイクルの確立
- 13.4 導入チェックリスト（設計・開発・デプロイ・運用の各フェーズ）

---

### 第IV部：最新動向 — いま起きていること

> 記事ベースの最新情報。本の鮮度を保つセクション（定期更新想定）

#### 第14章：実際のインシデントに学ぶ
- 14.1 OpenClaw危機（2026年初頭）— 135,000 Stars、21,000脆弱インスタンス
- 14.2 LiteLLM サプライチェーン汚染（2026年3月）— 3時間で300GB流出
- 14.3 MCP経由の攻撃事例
- 14.4 Adversa AI報告：35%が単純プロンプトで攻撃成功、10万ドル超損失
- 📰 既存記事の活用：mcp_trust_model, echoleak, claude_code_apt, memory_poisoning 等

#### 第15章：サプライチェーンセキュリティの最前線
- 15.1 Sleeper Agents攻撃（99.9%正常、特定トリガーで発動）
- 15.2 MCPサーバーエコシステムの脆弱性（OSS MCPサーバーの5%に既存）
- 15.3 AI-BOM（AI拡張SBOM）の動向
- 15.4 SAST/SCA/DASTのエージェント適用

---

### 第V部：未来編 — これから何が起きるか

> 中長期の技術・社会変化を見据えた考察

#### 第16章：自律エージェントの法的責任
- 16.1 現行法の限界と新法の動き
  - California AB 316 / Colorado AI Act / EU新製造物責任指令
- 16.2 代理法（Agency Law）のAIエージェント適用
- 16.3 保険・損害賠償の新パラダイム

#### 第17章：AGI時代のガバナンス
- 17.1 Legal Alignment for Safe AI（Oxford研究）
- 17.2 自律エージェントの行動制約設計
  - Constitutional AI / Corrigibility / キルスイッチ
- 17.3 NHI 450億超時代のスケーリングガバナンス
- 17.4 分散型エージェントガバナンス（DID/フェデレーション）

#### 第18章：エージェントエコシステムの未来
- 18.1 プロトコル標準化競争（A2A vs MCP の行方）
- 18.2 エージェントマーケットプレイスのセキュリティ
- 18.3 2029年予測：企業の70%がIT運用にエージェントAI導入
- 18.4 残された課題と読者への提言

---

## 既存記事の活用方針

| 既存記事/章 | 新構成での位置づけ |
|---|---|
| 01-introduction | → 第1章に統合・再編 |
| 02-paradigm-shift | → 第1章コラム「Lethal Trifecta」等に活用 |
| 03-owasp-agentic-top10 | → 第2章の骨格として活用 |
| 04-prompt-injection | → 第4章に統合・大幅加筆 |
| 05-mcp-security | → 第5章に統合 |
| 06-mcp-trust-boundary | → 第5章に統合 |
| 07-emerging-threats | → 第IV部（最新動向）に分散 |
| 08-real-world-incidents | → 第14章に統合 |
| 09-nhi-and-authority | → 第6章に統合・大幅加筆 |
| 10-japan-regulations | → 第3章に統合 |
| 11-team-governance | → 第9章に統合 |
| 12-coding-agent-security | → 第8章に統合 |
| 13-security-tools | → 各章の「ツール紹介」に分散 |
| 14-enterprise-roadmap | → 第13章に統合 |
| 15-future-risks | → 第V部に分散 |

## aigis 登場ポイント（裏KPI）

aigisが技術的に対応できる領域のみ、他ツールと並列で紹介：

| 章 | aigis の紹介内容 | 対応可能な範囲 |
|---|---|---|
| 第4章 | 入出力スキャン（64パターン、日本語対応、100%ベンチマーク精度） | プロンプトインジェクション検出・PII検出 |
| 第5章 | Claude Code hook統合によるMCPツール呼び出し事前スキャン | PreToolUse hookでの検査 |
| 第6章 | YAMLポリシーによるアクセス制御 | ポリシーベースのallow/deny/review |
| 第8章 | Claude Code PreToolUse hookによるコマンド実行前スキャン | シェルコマンド・ファイル操作のブロック |
| 第9章 | YAMLポリシーエンジン + 業種別テンプレート | ポリシー as Code の実装例 |
| 第11章 | 3層アクティビティストリーム + コンプライアンスレポート | ログ・監査・24規制要件マッピング |
| 第12章 | `aig benchmark`（検出精度テスト） | 自社のセキュリティベースライン測定 |

**紹介しない章**（aigisの対応範囲外）：
- 第6章のSPIFFE/Vault → HashiCorp等を紹介
- 第7章のA2A/マルチエージェント → Microsoft Agent Governance Toolkit等
- 第10章のHITL → Temporal/ワークフローエンジン
- 第15章のサプライチェーン → Snyk/SBOM系ツール
- 第16-18章の法規制/AGI → ツール紹介なし（考察中心）

---

## 次のステップ

1. **この構成案のレビュー・合意**
2. **第I部（基礎知識編）の執筆** — 本の土台となる部分を最優先
3. **各章の詳細アウトラインと参考文献リスト作成**
4. **既存記事の再編・加筆作業**
5. **aigisツール紹介セクションのドラフト**
