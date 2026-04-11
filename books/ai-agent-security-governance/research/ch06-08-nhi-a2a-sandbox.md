# 第6-8章 ファクトシート：NHI管理・マルチエージェント通信・サンドボックス

---

## 第6章：NHI管理とゼロトラスト

### 1. NHIの現状データ

**NHI数の統計**
- 「人間IDの25〜50倍」: Astrix Security, CyberArk等の複数ベンダーが2023-2024年に引用。業界コンセンサス（単一学術出典なし）
- 「2026年末450億超」→ ⚠️ カットオフ内で正確な出典未確認。Gartner 2024予測「2025年末までにNHIが750億」との混同可能性あり

**主要インシデント** 【確度: 高】

| インシデント | 日付 | 内容 | 出典 |
|---|---|---|---|
| Cloudflare Okta侵害 | 2024年1月 | Okta流出サービストークンでAtlassian環境侵入。NHIトークン未ローテーション | Cloudflare Blog 2024-02-02 |
| Microsoft Midnight Blizzard | 2024年1月 | レガシーOAuthアプリ（NHI）経由でExchange Online侵入 | Microsoft Security Blog 2024-01-19 |
| CircleCI侵害 | 2023年1月 | セッショントークンからOAuth/サービスアカウントキー窃取 | CircleCI Blog 2023-01-13 |

**予測データ**
- Gartner (2024): 「2026年までにセキュリティ障害の75%がID管理不備に起因」（2023年は50%）
- CyberArk 2024報告: 回答者の93%が過去1年で2件以上のID関連侵害を経験

### 2. SPIFFE/SPIRE 【確度: 高】

- CNCFの graduated プロジェクト（2022年9月）
- SPIFFE ID形式: `spiffe://<trust-domain>/<workload-identifier>`
- SVID: X.509証明書（SAN内にURI SAN）またはJWT（`sub` claim）
- SPIRE: 参照実装。Server（CA）+ Agent（各ノードでattestation）
- 出典: https://spiffe.io/ , https://github.com/spiffe/spiffe/tree/main/standards

**HashiCorp Vault SPIFFE対応**
- Vault 1.17 (2024年6月GA): PKI secrets engineでX.509-SVID発行可能
- Vault 1.21「SPIFFE認証ネイティブ」→ ⚠️ カットオフ後の可能性。要確認

### 3. OAuth 2.0のエージェント適用 【確度: 高】

- Client Credentials Flow: RFC 6749 Section 4.4
- Resource Indicators: RFC 8707 (2020年2月)
  - `resource`パラメータでトークン対象を限定
  - エージェントが複数API呼び出し時に特に重要

**Workload Identity Federation 比較**

| 項目 | GCP | AWS | Azure |
|------|-----|-----|-------|
| 機能名 | WIF | IAM Roles Anywhere | WIF |
| 発表 | 2021年4月GA | 2022年7月 | 2024年GA |
| SPIFFE対応 | OIDC経由マッピング | X.509-SVIDで使用可 | OIDC経由間接 |

### 4. ゼロトラスト

**Zero Standing Privileges (ZSP)** 【確度: 高】
- 定義: 常時付与の特権をゼロにし、JITで最小権限を一時付与
- 推進者: CyberArk, BeyondTrust, Delinea, Gartner
- 実装パターン:
  1. JIT Access（例: Azure PIM）
  2. JEA (Just Enough Administration)
  3. Ephemeral Credentials（例: Vault Dynamic Secrets）

**Microsoft ZT4AI** → ⚠️ カットオフ後。名称・内容未確認
**CSA Agentic Trust Framework** → ⚠️ 発行状況未確認

---

## 第7章：マルチエージェント通信セキュリティ

### 1. A2Aプロトコル 【確度: 高】

- **発表**: 2025年4月9日（Google Cloud Next '25）
- 出典: https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/
- GitHub: https://github.com/google/A2A

**技術仕様**
- HTTP + JSON-RPC 2.0、SSEストリーミング
- **Agent Card**: `/.well-known/agent.json` で能力を公開
- **Task**: ステートマシン（submitted → working → completed/failed）
- 認証: Agent Card内で宣言（OAuth 2.0, API Key, OIDC等）

**パートナー（2025年4月発表時、50社以上）**
- クラウド: Google, Salesforce, SAP, ServiceNow, Workday, Intuit
- AI: Anthropic, Cohere, LangChain, LlamaIndex, CrewAI
- エンタープライズ: Atlassian, Box, MongoDB, Elastic
- セキュリティ: CyberArk, Palo Alto Networks
- コンサル: Deloitte, Accenture, BCG, McKinsey, KPMG

**Linux Foundation移管（2025年6月）** → ⚠️ カットオフ後。要確認
**100社超** → 発表時は約50社。追加参画で増加した可能性

### 2. MCP vs A2A 【確度: 高】

Googleの公式説明:
> "A2A is designed to complement agent-to-tool protocols like MCP. While MCP focuses on connecting agents to tools and data sources, A2A focuses on enabling agents to communicate and collaborate with each other."

| 項目 | MCP | A2A |
|------|-----|-----|
| 提唱者 | Anthropic (2024年11月) | Google (2025年4月) |
| 目的 | エージェント ↔ ツール/データ | エージェント ↔ エージェント |
| アナロジー | USB-C（デバイス接続） | 外交プロトコル（主体間交渉） |
| 通信 | クライアント→サーバ | ピアツーピア |
| 主要抽象 | Tools, Resources, Prompts | Tasks, Agent Cards, Artifacts |
| 状態管理 | ステートレス | ステートフル |

**併用パターン**: オーケストレータがA2Aで専門エージェントに委任 → 各エージェントがMCPでツールにアクセス

### 3. マルチエージェントセキュリティ脅威

**脅威モデル**
- Confused Deputy: 悪意あるエージェントからの指示で特権操作実行
- Privilege Escalation Chain: 委任過程で権限累積
- Agent Impersonation: なりすましエージェントの参加
- Data Exfiltration: 正規通信チャネル経由のデータ窃取
- 関連論文: Greshake et al. (arXiv:2302.12173), Fang et al. (arXiv:2402.06664)

**Microsoft Agent Governance Toolkit** → ⚠️ Ed25519暗号ID + SPIFFE/SVID対応、<0.1msポリシーエンジン等の仕様はカットオフ後の可能性。Microsoft Build 2025 (2025年5月) 以降の発表と推測

---

## 第8章：コード実行とサンドボックス

### 1. 実行隔離技術の比較 【確度: 高】

| 技術 | 隔離レベル | 起動時間 | メモリOH | セキュリティ境界 |
|------|-----------|---------|---------|----------------|
| Docker | Namespace+cgroups | ~1s | ~10MB | カーネル共有（弱） |
| Firecracker | microVM (KVM) | ~125ms | ~5MB/VM | HW仮想化（強） |
| Kata Containers | VM内コンテナ | ~1s | ~40-100MB | HW仮想化（強） |
| gVisor | ユーザ空間カーネル | ~数百ms | ~20-50MB | syscallフィルタ（中〜強） |
| Wasm | Wasm VM | ~1ms | ~数MB | メモリ安全+capability（強） |

出典:
- Firecracker: "Lightweight Virtualization for Serverless Applications" (NSDI '20)
- gVisor: https://gvisor.dev/
- Kata: https://katacontainers.io/

### 2. コーディングエージェントのセキュリティ 【確度: 高】

**Claude Code**
- 許可制モデル: 書込み・コマンド実行・ネットワークはユーザー承認必要
- `.claude/settings.json`で許可/拒否設定
- 出典: https://docs.anthropic.com/en/docs/claude-code/security

**Cursor**
- ローカルIDE（VS Code fork）、Privacy Mode、SOC 2 Type II取得
- コマンド実行はユーザー承認必要、diff レビュー表示

**GitHub Copilot Coding Agent**
- GitHub Actions ランナー（Firecracker VM）上で実行
- リポジトリスコープ限定、PRとしてdiff提出
- 出典: GitHub Blog 2025年2月 "GitHub Copilot: the agent awakens"

**Devin** (Cognition AI)
- 隔離クラウドVM内でブラウザ・ターミナル・エディタ動作
- SOC 2対応。ネットワーク制御設定可能

### 3. クラウドサンドボックス比較 【確度: 高】

| サービス | 隔離技術 | 起動時間 | 特徴 |
|---------|---------|---------|------|
| **E2B** | Firecracker | 150-300ms | AIエージェント専用、OSS (Apache 2.0) |
| **Modal** | gVisor | ~1s cold | GPU対応、ML特化、SOC 2 |
| **AWS Lambda** | Firecracker | 成熟 | 15分制限、最大規模 |
| **Cloudflare Workers** | V8 Isolates | ~0ms | JS/Wasm限定、超低レイテンシ |

---

## 要検証事項

- [ ] NHI「2026年末450億超」の正確な出典
- [ ] HashiCorp Vault 1.21 SPIFFE認証ネイティブの確認
- [ ] Microsoft ZT4AI の名称・内容
- [ ] CSA Agentic Trust Framework の発行状況
- [ ] A2A Linux Foundation移管の正式発表
- [ ] Microsoft Agent Governance Toolkit の詳細仕様
- [ ] Forrester Wave: NHI Security Q4 2024 の発行確認
