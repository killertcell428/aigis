# 第9-13章 ファクトシート：実践編

---

## 第9章：ガバナンス体制

### 1. ガバナンス成熟度データ

**「成熟したガバナンスを持つ企業は約20%」**
- Gartner 2023年AI調査: AIガバナンスを「成熟」レベルで運用している組織は約20-25%
  - 出典: Gartner "AI Governance: A Framework for Managing Risk" (2023-2024)
  - ⚠️ 具体数値は有料レポート内。公開情報では確認困難

**「エージェント管理戦略を持つ組織は10%」**
- Gartner Predicts 2025: 「2028年までにエンタープライズの33%がエージェンティックAIを本番運用」
- 2024時点での管理戦略保有率10%は推計との整合あり
- ⚠️ 正確な出典未確定（複数アナリストレポートの合成値の可能性）

**関連レポート**
- Deloitte "State of AI in the Enterprise, 6th Edition" (2024): AIガバナンス成熟度別分類
- McKinsey "The State of AI in 2024" (2024年5月): AI採用組織の72%がガバナンスポリシー保有

### 2. ポリシーエンジン 【確度: 高】

**OPA (Open Policy Agent)**
- CNCF卒業プロジェクト（2021年2月）
- Rego言語でポリシー記述
- 主要ユースケース: API認可、K8s admission control
- ⚠️ AIエージェント固有の公開適用事例は限定的

**AWS Cedar**
- 発表: 2023年5月（AWS re:Inforce 2023）、OSS
- 型付きポリシー言語、RBAC+ABACハイブリッド
- 形式検証（automated reasoning）による正確性保証
- Amazon Verified Permissionsと統合

### 3. AI CoE 成功事例 【確度: 中】

- JPMorgan Chase: AI CoE設立、LLM Suiteを社内展開、社員の約60%が利用
- Walmart: AI/ML CoEでサプライチェーン最適化
- Shell: 1,000以上のAIユースケースを管理

---

## 第10章：Human-in-the-Loop

### 1. 3つの基本パターン

⚠️ Approval Gate / Escalation Trigger / Tiered Escalation を3つセットで定義した単一学術論文は未特定。実務的分類

**関連文献**
- Shneiderman, B. (2022) "Human-Centered AI" — HCAI文脈での人間監視レベル定義
- Amershi, S. et al. (2019) "Guidelines for Human-AI Interaction" CHI 2019 — 18のガイドライン
- LangGraph: human-in-the-loop ノードとしてApproval Gateパターン実装
  - https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/

### 2. 制度的要件 【確度: 高】

**EU AI Act 第14条 "Human oversight"**
- 出典: Regulation (EU) 2024/1689
- 要点:
  - Art. 14(1): 高リスクAIは人間の監視を可能にする設計
  - Art. 14(3)(a): 監視者がAIの能力と限界を適切に理解
  - Art. 14(4): 監視者がAI使用を停止できるメカニズム
  - 監視者はAI出力を無視・上書き・停止する権限を持つ

**NIST AI RMF**
- GOVERN: 適切な人間の監視を組織レベルで定義
- MAP 1.6: 人間-AI相互作用とフィードバック仕組みの記述
- MEASURE 2.6: 人間介入プロセスの評価

### 3. 自動化バイアス研究 【確度: 高】

- Parasuraman & Manzey (2010): Human Factors, 52(3), 381-410 — 自動化バイアスの基礎研究
- Goddard et al. (2012): JAMIA, 19(1), 121-127 — 系統的レビュー、臨床意思決定支援でのエビデンス

---

## 第11章：監査・オブザーバビリティ

### 1. OpenTelemetry GenAI 【確度: 高】

- リポジトリ: https://github.com/open-telemetry/semantic-conventions/tree/main/docs/gen-ai
- ステータス: Experimental (2024-2025年)
- 属性: `gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens/output_tokens`等
- OpenLLMetry (Traceloop): https://github.com/traceloop/openllmetry

### 2. プラットフォーム比較 【確度: 中（価格は変動）】

| 項目 | LangSmith | LangFuse | Helicone | Braintrust |
|------|-----------|----------|----------|------------|
| 開発元 | LangChain | OSS | Helicone | Braintrust |
| 特徴 | LangChain統合、デバッグUI | OSS、セルフホスト可 | プロキシベース、簡単 | Eval特化 |
| 価格帯 | Free + $39/seat/mo~ | OSS無料 / $59/mo~ | Free + 従量制 | Free + $250/mo~ |
| セルフホスト | 不可 | 可能 | 可能 | 不可 |

**エンタープライズ**
- Datadog AI Observability: 2024年GA。LLMトレース、コスト追跡、品質評価
- Dynatrace: Davis AI統合。エージェント専用機能は発展途上

---

## 第12章：レッドチーミング

### 1. 統計データ

**「攻撃成功率81%」** → ⚠️ 正確な出典未確認
- NIST AI 100-2 E2023 (2024年1月) 自体にはこの数字なし
- DEF CON 31 AI Red Team (2023年8月): 2,200人参加のLLM攻撃実験。81%はこの実験からの可能性

**Adversa AI「35%/10万ドル」** → ⚠️ 出典レポート特定困難
- Adversa AI "AI Security Report" シリーズの可能性
- 確認推奨: https://adversa.ai/blog/

### 2. 自動化レッドチーミングツール 【確度: 高】

| ツール | 開発元 | 特徴 |
|--------|--------|------|
| **Garak** | NVIDIA | LLM脆弱性スキャナ、プラグインアーキテクチャ。OSS (2023年) |
| **DeepEval/DeepTeam** | Confident AI | LLM評価+レッドチーミング。https://github.com/confident-ai/deepeval |
| **Promptfoo** | Promptfoo | YAML設定ベース、CI/CD統合容易。`promptfoo redteam` |
| **PyRIT** | Microsoft | 自動レッドチーミング、マルチモーダル。OSS (2024年2月) |

### 3. EU AI Act のレッドチーミング義務 【確度: 高】

- Art. 9(6-7): 高リスクAIのテスト義務
- Art. 55(1): システミックリスクGPAIに adversarial testing 義務
- Recital 110: レッドチーミングを adversarial testing の具体例として明示

---

## 第13章：エンタープライズ導入ロードマップ

### 1. 先行事例

**成功**: Microsoft Copilot段階展開（2023年後半〜）、Capital One MLリスク管理フレームワーク
**失敗**:
- Samsung (2023年4月): ChatGPTに機密ソースコード入力→情報漏洩→社内利用禁止
- Air Canada (2024年2月): チャットボット誤案内→裁判で賠償命令

### 2. コスト・ROI 【確度: 高】

**IBM Cost of a Data Breach Report 2024** (2024年7月)
- URL: https://www.ibm.com/reports/data-breach
- データ侵害平均コスト: **488万ドル**（過去最高、前年比10%増）
- AI・オートメーション活用組織: 平均 **176万ドル** のコスト削減
- 特定・封じ込め平均: **258日**
- AIセキュリティツール広範使用: **381万ドル** vs 未使用 **507万ドル**

---

## 要検証事項

- [ ] 「成熟したガバナンス20%」の正確なGartner出典
- [ ] 「エージェント管理戦略10%」の出典
- [ ] 攻撃成功率81%の正確な出典
- [ ] Adversa AI 35%/10万ドルの出典レポート
- [ ] OpenTelemetry GenAI Semantic Conventions の最新ステータス
- [ ] 各プラットフォーム価格の最新確認
