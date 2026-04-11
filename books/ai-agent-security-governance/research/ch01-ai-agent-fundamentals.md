# 第1章 ファクトシート：AIエージェントとは何か — セキュリティの視点から

## 1. AIエージェントの定義

### 主要企業・研究機関の公式定義

**Anthropic**
- 「LLMがツールを使い、環境からのフィードバックに基づいてループ処理を行うシステム」
- "agentic systems" を広義に捉え、LLMが動的にワークフローを制御するものを "agents"、固定的なコードフローでLLMを呼ぶものを "workflows" と区別
- 出典: https://www.anthropic.com/research/building-effective-agents（2024年12月）

**OpenAI**
- 「instructions, knowledge, actionsの3要素を持ち、LLMを中核としてツール呼び出しとフィードバックループで自律的にタスクを遂行するシステム」
- 出典: https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf（2025年3月）

**Google DeepMind**
- 「環境を観察し、ツールを使って行動し、目標達成に向けて自律的に推論・計画するアプリケーション」
- 3コンポーネント: モデル（model）、ツール（tools）、オーケストレーション層（orchestration layer）
- 出典: Google Cloud "Agents" whitepaper（2024年9月頃）

**NIST**
- AI 100-2 E2023: AIシステムへの攻撃分類を体系化。エージェント固有の定義は直接的には示されていないが「自律的意思決定システム」へのリスクフレームワークを提供
- AI RMF 1.0: 自律性のレベルに応じたリスク管理を提唱
- 出典: https://csrc.nist.gov/pubs/ai/100/2/e2023/final（2024年1月）

**EU AI Act**
- "AI system" を広義に定義。GPAI（General-purpose AI models）の規定あり
- エージェント固有の定義は明示されていないが、高リスクAIシステムの分類においてautonomyレベルが評価基準に含まれる
- 出典: Regulation (EU) 2024/1689（2024年7月12日官報掲載）

### エージェント vs チャットボット vs アシスタント

| 特性 | チャットボット | アシスタント | エージェント |
|------|-------------|------------|------------|
| 対話モデル | 1問1答（stateless） | 文脈保持型対話 | 目標駆動型の自律行動ループ |
| ツール使用 | なし〜限定的 | 限定的 | 広範（コード実行、ファイル操作、外部API群） |
| 自律性 | 受動的 | 半自律的 | 自律的（計画→実行→評価→修正） |
| 状態管理 | セッション単位 | セッション〜永続 | 永続メモリ＋環境状態の能動的管理 |
| 行動の影響 | テキスト応答のみ | テキスト＋限定的副作用 | 実世界への不可逆な副作用を伴う |

### 学術的分類

- **Russell & Norvig "AIMA"**: Simple reflex / Model-based reflex / Goal-based / Utility-based / Learning agents
- **Wooldridge & Jennings (1995)**: autonomy, social ability, reactivity, pro-activeness の4特性
  - 出典: The Knowledge Engineering Review, 10(2), 115-152

---

## 2. エージェントのアーキテクチャパターン

### ReAct（Reasoning + Acting）
- Yao et al., ICLR 2023
- Thought→Action→Observationのトレースを交互に生成
- arXiv: https://arxiv.org/abs/2210.03629

### Plan-and-Execute
- Wang et al., ACL 2023 "Plan-and-Solve Prompting"
- BabyAGI (Yohei Nakajima, 2023年4月) が実装例

### Tool-use（Function Calling）
- OpenAI 2023年6月にFunction Calling導入、Anthropic 2024年にTool Use API
- Toolformer: Schick et al., NeurIPS 2023. arXiv: https://arxiv.org/abs/2302.04761

### Multi-Agent
- CAMEL: Li et al., NeurIPS 2023. arXiv: https://arxiv.org/abs/2303.17760
- Generative Agents: Park et al., UIST 2023. arXiv: https://arxiv.org/abs/2304.03442

### 主要フレームワーク

| フレームワーク | 開発元 | 設計思想 |
|---|---|---|
| LangGraph | LangChain社 | ワークフローを有向グラフで表現。状態の明示的管理、HITL設計可能 |
| CrewAI | Joao Moura | ロールベースのマルチエージェント。role/goal/backstory付与 |
| AutoGen | Microsoft Research | マルチエージェント会話。人間エージェント参加可能。コード実行統合 |

---

## 3. 従来AIとエージェントAIのセキュリティの違い

### 攻撃面の比較

| 観点 | 従来AI（静的推論） | エージェントAI（動的行動） |
|------|-------------------|------------------------|
| 入力 | ユーザープロンプトのみ | プロンプト＋ツール出力＋メモリ＋外部データ |
| 出力 | テキスト応答 | テキスト＋API呼び出し＋コード実行＋ファイル操作 |
| 影響範囲 | 情報漏洩・誤情報 | 実世界への不可逆な操作 |
| 攻撃の連鎖 | 単発 | マルチステップ攻撃チェーン |
| 持続性 | セッション限定 | 永続メモリ汚染が将来のセッションに影響 |

### 「Lethal Trifecta」（要出典確認）
- Simon Willison が警告する3要素: **access to tools + access to untrusted data + autonomy**
  - 出典: https://simonwillison.net/（2023-2024年、複数記事）
- Johann Rehberger も "toxic combination" として警告
- ⚠️ "Lethal Trifecta" という用語自体の初出典は未確定。独自概念として提示するか出典を特定する必要あり

### 攻撃面の4層モデル（各層の学術的根拠）

1. **プロンプト層**: Greshake et al., 2023. arXiv:2302.12173
2. **ツール層**: OWASP LLM Top 10 "Excessive Agency" (LLM09)
3. **メモリ層**: Zou et al., "PoisonedRAG", 2024. arXiv:2402.07867
4. **通信層**: マルチエージェント通信セキュリティ（比較的新しい研究領域）
- ⚠️ 4層モデル自体は特定の単一論文に基づくものではない

---

## 4. 脅威モデリングの基礎

### MITRE ATLAS
- 正式名称: Adversarial Threat Landscape for AI Systems
- ATLAS v4.0 (2024年10月時点): 14戦術、約80+技法
- 出典: https://atlas.mitre.org/

### STRIDE/DREAD のエージェント拡張
- Microsoft "Threat Modeling AI/ML Systems and Dependencies"（2021年）
- Microsoft + BerkmanKlein Center "Failure Modes in Machine Learning"（2022年）
- 出典: https://learn.microsoft.com/en-us/security/engineering/threat-modeling-aiml

### エージェント固有の攻撃面に関する主要論文

| 論文 | 著者 | 内容 | arXiv |
|---|---|---|---|
| ToolEmu | Ruan et al., 2023 | LLMエージェントリスクのサンドボックス評価 | 2309.15817 |
| AgentDojo | Debenedetti et al., 2024 | 攻撃・防御の動的評価ベンチマーク | 2406.13352 |
| LLM Agent Survey | Xi et al., 2023 | LLMベースエージェントの包括的サーベイ | 2309.07864 |
| Morris II (AI Worm) | Cohen et al., 2024 | エージェント間伝播型ワーム攻撃の概念実証 | Cornell Tech/Technion |

---

## 5. 市場データ

### Gartner
- 「2028年までに日常業務の意思決定の少なくとも15%がAgentic AIで自律的に行われる」（2024年時点ほぼ0%）
- 「2028年までにエンタープライズソフトウェアの33%がAgentic AI搭載」（2024年時点1%未満）
- Agentic AI = Gartner 2025年戦略的テクノロジートレンド1位
- 出典: https://www.gartner.com/en/articles/gartner-top-10-strategic-technology-trends-for-2025（2024年10月）

### McKinsey
- 生成AI全体で年間2.6兆〜4.4兆ドルの経済価値（2023年6月）
- エージェント固有の数値は2023年時点では切り出されていない

### Capgemini
- 「2025年までに企業の82%がAIエージェントの統合を計画」（出典の正確なタイトル・日付は要検証）

### エンタープライズ導入状況
- Microsoft: Fortune 500の60%以上がCopilot使用（2024年時点）
- Salesforce: Agentforce 発表（2024年9月）、1億件以上のエージェントインタラクション
- ServiceNow, SAP, Oracle も2024年後半からAgentic AI機能発表

---

## 要検証事項

- [ ] "Lethal Trifecta" の正確な初出典
- [ ] 4層攻撃面モデルの学術的根拠（独自概念として提示するか検討）
- [ ] MITRE ATLAS の2026年最新版の戦術数・技法数
- [ ] Gartner/Capgeminiの数値を原文レポートで裏取り
- [ ] 2026年時点のエンタープライズ導入実績データの更新
