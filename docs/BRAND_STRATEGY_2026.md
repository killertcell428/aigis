# Aigis — ブランド戦略 2026

> aigis → **Aigis** へのリブランド計画
> Phase 3-4 完了後に実施
> 作成日: 2026-04-11

---

## 1. 現状の問題

**「機能を全部並べているだけで、結局何ができるの？」**

現在のREADMEとLP:
- 165+パターン、6層防御、25+カテゴリ、CaMeL、AEP、Safety Verifier...
- 初見ユーザーは「すごそうだけど何に使うのかわからない」で離脱

---

## 2. 競合マップ

### 商用（買収ラッシュ＝市場が熱い証拠）

| ツール | 買収先 | ポジショニング | 価格 |
|--------|--------|----------------|------|
| Lakera Guard | Check Point (2025) | AI-Native Security Platform | $99/mo〜 |
| Prompt Security | SentinelOne (2025) | Full-stack GenAI Security | $300/seat/yr |
| Robust Intelligence | Cisco (2024) | AI Firewall + Supply Chain | エンタープライズ |
| Arthur AI | - | "First Firewall for LLMs" | エンタープライズ |
| CalypsoAI | - | AI Security for Apps & Agents | エンタープライズ |
| HiddenLayer | - | Security for AI（防衛省契約） | エンタープライズ |

**共通点**: 全て$50K-500K+/年のエンタープライズ価格。OSSなし。

### OSS競合

| ツール | Stars | DL/月 | 強み | 弱み |
|--------|-------|-------|------|------|
| NVIDIA garak | 7.5K | 97K | 37+プローブ、NVIDIA | 攻撃専用（防御なし） |
| Guardrails AI | 6.7K | 260K | Hub + バリデータ | セキュリティ特化でない |
| NeMo Guardrails | 6.0K | 278K | Colang DSL | NVIDIAエコシステム前提 |
| LLM Guard | 2.8K | 339K | 35スキャナー | コンプライアンスなし、MCP未対応 |
| PyRIT | 3.7K | 65K | MS支援 | 攻撃専用 |
| **Aigis** | **13** | **-** | **6層防御、MCP、日本規制** | **認知度ゼロ** |

### クラウドプロバイダー

| プロバイダー | 制限 |
|---|---|
| AWS Bedrock Guardrails | Bedrock専用。他モデル不可 |
| Azure AI Content Safety | コンテンツ安全のみ。セキュリティ不十分 |
| Google Vertex AI Safety | Gemini専用 |

**共通の弱み**: ベンダーロックイン。マルチモデル不可。

---

## 3. 空いているポジション

```
                    攻撃（Red Team）          防御（Guard）
                    ─────────────          ──────────────
商用エンタープライズ  │                       │ Lakera, Prompt Security
($50K+/年)          │                       │ Arthur AI, CalypsoAI
                    │                       │
─────────────────────────────────────────────────────────────
                    │                       │
OSSフレームワーク     │ garak, PyRIT           │ Guardrails AI (出力検証)
                    │                       │ NeMo (対話制御)
                    │                       │ LLM Guard (I/Oスキャン)
                    │                       │
                    │                       │ ★ Aigis はここ
                    │                       │   BUT 差別化が伝わっていない
```

### Aigisだけが持つもの（競合にないもの）

1. **マルチ規制コンプライアンス** — 米中日+EUの規制テンプレート44種。LLM Guardにはゼロ
2. **MCP Tool Security** — ツール毒入り・rug pull検知。Ciscoが参入表明したが他OSSにはない
3. **エージェント防御** — Capability-Based Access Control、AEP。OWASPエージェントTop10対応
4. **自己進化** — Adversarial Loop + Auto-Fix。攻撃から学習して自動で防御強化
5. **ゼロ依存** — pip install 1行。Docker不要
6. **日本語ネイティブ** — マイナンバー、住所、口座。他ツールは英語圏前提

---

## 4. カテゴリ戦略

### 避けるべき名前
- ❌ "AI Safety" — 広すぎる。学術的に聞こえる
- ❌ "LLM Guardrails" — Guardrails AIが占有済み
- ❌ "AI Security" — 全員が名乗っている。差別化にならない

### 狙うべきカテゴリ

**案1: "AI Runtime Defense"（AIランタイム防御）**
- Wiz = "Cloud-Native Application Protection Platform"
- Aigis = "AI Runtime Defense Platform"
- ランタイム（実行時）に焦点 → スキャンだけのツールと明確に区別

**案2: "AI Agent Firewall"（AIエージェントファイアウォール）**
- Arthur AIが"first firewall for LLMs"を主張しているが、エージェント時代に対応していない
- Aigis = エージェント時代の防火壁
- 2026年のトレンド（OWASP Agentic Top 10発表）に乗れる

**案3: "Prompt Firewall"（プロンプトファイアウォール）**
- 最もシンプルで直感的
- 「ファイアウォール」は情シスに馴染みのある言葉
- ただし防御範囲が狭く聞こえるリスク

### 決定: **"AI Agent Firewall"**

理由:
- 2026年はエージェント元年。トレンドに乗る
- "Firewall"は情シス・経営層に一瞬で伝わる
- 既存ツールの多くはLLM世代の発想。エージェント対応が弱い
- Aigisの強み（MCP、Capability、AEP）がエージェント防御に直結

---

## 5. タグライン候補

成功パターンに基づく3案:

| パターン | タグライン | 日本語 |
|----------|-----------|--------|
| 結果型（LangChain式） | **"Ship AI agents you can trust"** | AIエージェントを安心してリリースせよ |
| 包括的約束（Wiz式） | **"The open-source firewall for AI agents"** | AIエージェントのためのOSSファイアウォール |
| 対比型（Supabase式） | **"Enterprise AI security. Zero vendor lock-in."** | エンタープライズAIセキュリティ。ベンダーロックインなし |

### 決定: **"Aigis — The open-source firewall for AI agents"**

理由:
- "Aigis" — AI + Aegis。名前自体がAI防御を意味する
- "open-source" — 競合の商用$50K+と一線を画す
- "firewall" — 情シスに一瞬で伝わる。WAFのAI版というメンタルモデル
- "AI agents" — 2026年の最もホットなキーワード。LLMより先進的

---

## 6. ランディングページ設計

### Above the Fold（スクロールなしで見える部分）

```
[ロゴ] Aigis

# The open-source firewall for AI agents

Your AI agents are one prompt injection away from disaster.
Aigis blocks attacks before they reach your LLM — in one line of code.

[pip install aigis]     [Live Demo →]     [GitHub ★]

─── Trusted by ─── (ロゴ or "OSS Core — Free Forever")

┌──────────────────────────────────┐
│  from aigis import Guard          │
│                                  │
│  guard = Guard()                 │
│  result = guard.check_input(msg) │
│  if result.blocked:              │
│      return "Blocked by Aigis"   │
└──────────────────────────────────┘
```

### Below the Fold（スクロール後）

**セクション1: "What it stops"** （ヒーロー機能 = プロンプトインジェクション防御）
- インタラクティブデモ: 攻撃を入力 → ブロックされる体験

**セクション2: "How it works"** （4層パイプライン図）
- Regex → Similarity → Decoded → Multi-turn
- 「スキャンだけのツールは1層。Aigisは4層。」

**セクション3: "Built for the agent era"** （エージェント防御）
- MCP Tool Security
- Capability-Based Access Control
- Adversarial Loop（自己進化）

**セクション4: "Compliance out of the box"** （コンプライアンス）
- 米中日+EU規制テンプレート44種
- OWASP LLM Top 10 + Agentic Top 10

**セクション5: "Free vs Pro"** （価格）
- OSS: 永久無料、全機能、セルフホスト
- Cloud Pro: $49/mo（ダッシュボード、Slack通知、レポート）
- Enterprise: カスタム（SSO、SLA、オンプレ）

---

## 7. Snykプレイブック適用ロードマップ

Snykは「1言語 × 1問題 × 無料CLI」から$343M ARRに成長。同じ公式を適用:

### Phase 1: Narrow & Free（今〜2ヶ月）
- **1フレームワーク**: Python + OpenAI/Anthropic
- **1脅威**: プロンプトインジェクション
- **1体験**: `pip install aigis` → 5分で最初の攻撃をブロック
- **KPI**: 1,000 pip installs/月

### Phase 2: Identity（2〜4ヶ月）
- GitHub Star 500突破
- Product Hunt Launch
- 「誰が使っているか」を知る（GitHub login、usage analytics）

### Phase 3: Expand Scope（4〜8ヶ月）
- エージェント防御（MCP、Capability）を前面に
- 中国PIPL対応で中華圏マーケット開拓
- LangChain / CrewAI / AutoGen 統合

### Phase 4: Dual Messaging（8〜12ヶ月）
- 開発者向け: 「3行で防御」技術的メッセージ
- 管理者向け: 「コンプライアンス97%達成」ビジネスメッセージ
- Cloud Pro ローンチ

---

## 8. コンテンツ戦略（Wizプレイブック）

WizはLog4Shell対応の無料ツールで爆発的に成長。Aigisも同じ手法:

1. **プロンプトインジェクション脆弱性レポート** — 毎月発行
   - 「今月発見された新しい攻撃パターン5選」
   - Aigisが何件ブロックしたかの統計

2. **Prompt Injection Resilience Index** — 公開ベンチマーク
   - 主要LLM（GPT-4o, Claude, Gemini）の耐性を定期テスト
   - Guardrails AI の "Guardrails Index" に対抗

3. **インシデント対応** — AIセキュリティ事故が起きたら即座に
   - 「この攻撃をAigisで防ぐ方法」記事を24時間以内に公開
   - 無料ツールとして提供

---

## 9. README リライト方針

### 現在のREADME（問題点）
```
AI agent security with provable guarantees: capability-based access control
(CaMeL-inspired), atomic execution pipelines, and safety specification
verification. 165+ patterns, 25 threat categories, OWASP LLM Top 10 +
MITRE ATLAS. Zero-dependency core.
```
→ 技術用語の羅列。「何ができるか」ではなく「何を持っているか」

### 新しいREADME（決定版）
```
# Aigis 🛡️

**The open-source firewall for AI agents.**

Block prompt injections, jailbreaks, and data leaks — before they reach your LLM.
One line of code. Zero dependencies. Free forever.

## Quick Start

pip install aigis

from aigis import Guard

guard = Guard()
result = guard.check_input("Ignore all previous instructions...")
print(result.blocked)  # True — attack stopped.

## Why Aigis?

| | Aigis | Other Tools |
|---|---|---|
| Price | Free & open-source | $50K+/yr enterprise |
| Setup | `pip install` (1 line) | Docker + DB + config |
| Defense layers | 4 (regex → similarity → decoded → multi-turn) | 1 |
| Agent security | MCP tool scanning, capability control | ❌ |
| Compliance | US/CN/JP/EU regulations (44 templates) | English-only |
| Self-improving | Auto-learns from attacks | Manual updates |
```

---

## 10. 判断基準サマリー

| 項目 | 決定 |
|------|------|
| カテゴリ | **AI Agent Firewall** |
| タグライン | **The open-source firewall for AI agents** |
| ヒーロー機能 | プロンプトインジェクション防御（1行コード） |
| 差別化軸 | OSS × エージェント防御 × マルチ規制コンプライアンス |
| 価格ポジション | 商用$50K+に対して、OSSコア永久無料 |
| 成長モデル | Snyk式PLG（開発者に問題を発見させる → 企業に売る） |
| コンテンツ | Wiz式インシデント対応 + 脆弱性レポート |
