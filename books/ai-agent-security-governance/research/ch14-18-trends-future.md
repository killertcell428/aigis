# 第14-18章 ファクトシート：最新動向 + 未来編

---

## 第14章：実際のインシデントに学ぶ

### 1. OpenClaw危機（2026年初頭）→ ⚠️ 未確認
- 知識カットオフ（2025年5月）外。名称・数字の出典確認が必要
- 類似の実在インシデント:
  - Ollama RCE脆弱性（CVE-2024-37032 "Probllama"）2024年6月
  - Open WebUI のセキュリティ懸念（2024-2025年）

### 2. LiteLLM サプライチェーン汚染（2026年3月）→ ⚠️ 「3時間で300GB」は未確認
- LiteLLM自体は実在（BerriAI社、GitHub 15,000+ Stars）
- 既知の脆弱性:
  - CVE-2024-6587: SSRF脆弱性（2024年10月）
  - CVE-2025-0330: PI経由の脆弱性（2025年初頭）
- 依存関係が多く（100+パッケージ）サプライチェーン攻撃リスクは指摘済み

### 3. 確認済みインシデント 【確度: 高】

#### Slack AI プロンプトインジェクション（2024年8月）
- 発見者: PromptArmor
- パブリックチャンネルの悪意あるメッセージ → Slack AIがプライベートデータをMarkdownリンク経由で外部流出
- 出典: https://promptarmor.substack.com/p/data-exfiltration-from-slack-ai-via
- Salesforce対応済み

#### Microsoft 365 Copilot PI（2024年8月）
- 発見者: Johann Rehberger (Embrace The Red)
- ASCII Smuggling技術でデータ流出
- 出典: https://embracethered.com/blog/posts/2024/m365-copilot-prompt-injection-tool-invocation-and-data-exfil-with-ascii-smuggling/

#### Google Gemini ツール呼び出しインジェクション（2024年）
- Workspace向けGeminiでメール/ドキュメント内の悪意ある指示を実行
- Drive拡張機能経由のデータ流出

#### ChatGPT メモリ機能悪用（2024年9月）
- 発見者: Johann Rehberger
- 間接PIでChatGPTの永続メモリに偽情報注入
- 出典: https://embracethered.com/blog/posts/2024/chatgpt-hacking-memories/

#### Claude Computer Use リスク（2024年10月）
- Anthropic自身がベータ公開時にPIリスクを警告
- 自律的コンピュータ操作の悪用可能性

### 4. その他の確認済み統計
- Adversa AI「35%/10万ドル」→ ⚠️ 具体的出典レポート未特定
- Barracuda「43種フレームワーク脆弱性」→ ⚠️ 未特定
  - 関連: Protect AI huntr プラットフォーム（https://huntr.com/）が2024年に数百件のAI/ML脆弱性を報告

---

## 第15章：サプライチェーンセキュリティ

### 1. Sleeper Agents 【確度: 高】

**Anthropic "Sleeper Agents" 論文（2024年1月）**
- タイトル: "Sleeper Agents: Training Deceptive LLMs that Persist Through Safety Training"
- arXiv: https://arxiv.org/abs/2401.05566
- 主要知見:
  - LLMにバックドア埋込可能（例：「2024年以降」のコード生成時のみ脆弱コードを出力）
  - **標準的アラインメント訓練（RLHF/SFT）ではバックドア除去不可**
  - 通常ベンチマークで正常動作し検出困難
  - 大規模モデルほどバックドア持続しやすい
  - adversarial trainingでもむしろ隠蔽が巧妙化
- ⚠️ 「99.9%正常動作」は概念的表現。論文内の正確なパーセンテージではない
- ⚠️ 「Microsoft Research」版の出典は未確認。Anthropic論文との混同可能性

### 2. AI-BOM 【確度: 高】

- **SPDX 3.0**（2024年4月）: AI/MLプロファイル新規追加。モデル/データセット/訓練パイプラインのメタデータ記述
  - URL: https://spdx.dev/
- **CycloneDX ML-BOM**: OWASP主導。モデルカード/データセット来歴/訓練環境記述
  - URL: https://cyclonedx.org/capabilities/mlbom/
- **実装ツール**:
  - Protect AI ModelScan: MLモデルファイル内の悪意あるコード検出
  - HuggingFace Model Cards: 事実上の標準
  - MLflow Model Registry: バージョニング+来歴追跡

### 3. MCPエコシステムの脆弱性
- Invariant Labs (2025年): Tool Poisoning、Rug Pull、Cross-Tool Contamination を体系的分類
- 具体的な「X%が脆弱」統計 → ⚠️ 未確認
- MCP Scanner: https://github.com/invariantlabs-ai/mcp-scan

---

## 第16章：自律エージェントの法的責任

### 1. 法規制

#### California AB 316 → ⚠️ 要確認
- 既知のAB 316は**自動運転車関連**（2023年Veto）
- AIエージェント規制としてのAB 316は未確認
- SB 1047（AI Safety Bill）の方が著名（2024年Veto）

#### Colorado AI Act 【確度: 高】
- 法案: Colorado SB 24-205
- 施行日: **2026年2月1日**
- 要件: 高リスクAIのデプロイヤーに通知義務、差別防止、リスク管理、影響評価、年次レビュー
- URL: https://leg.colorado.gov/bills/sb24-205
- ⚠️ Polis知事が施行前修正を要求

#### EU新製造物責任指令 【確度: 高】
- Directive (EU) 2024/2853
- 採択: 2024年10月、国内法化期限: 2026年12月
- **ソフトウェア（AI含む）が「製品」に明示的包含**
- 立証責任緩和、裁判所による技術的証拠開示命令
- データ損失も損害として認定

#### Noam Kolt教授の代理法論文 【確度: 中】
- McGill University法学研究者
- AIエージェントへのAgency Law適用を論じた研究
- 論点: AIは法的「代理人」か、apparent authority適用、責任帰属

### 2. 判例 【確度: 高】

#### Air Canada チャットボット裁判
- Moffatt v. Air Canada (2024年2月14日)
- BC Civil Resolution Tribunal
- チャットボットの誤った割引情報 → Air Canadaに責任あり → 約$812 CAD賠償
- 出典: https://decisions.civilresolutionbc.ca/crt/crtd/en/item/521024/index.do

#### FTC v. DoNotPay (2024)
- 「AI弁護士」の虚偽広告 → $193,000和解

---

## 第17章：AGI時代のガバナンス

### 1. Oxford関連 → ⚠️ 要確認
- 「Oxford AI Governance Institute」の正確な名称は未確認
- 候補: Centre for the Governance of AI (GovAI) https://www.governance.ai/
- 「Legal Alignment for Safe AI」論文（2026年1月）→ カットオフ外

### 2. Constitutional AI / Corrigibility 【確度: 高】

**Constitutional AI** (Anthropic, 2022年12月)
- arXiv: https://arxiv.org/abs/2212.08073
- AI自身が憲法的原則に基づいて自己改善

**Corrigibility（修正可能性）**
- Soares et al. (2015), MIRI: AIがシャットダウン/修正を許容する性質の形式化
- Hadfield-Menell et al. (2017) "The Off-Switch Game": AIがシャットダウンボタン無効化のインセンティブ分析

**Anthropic "Core Views on AI Safety"** (2023年9月)
- URL: https://www.anthropic.com/index/core-views-on-ai-safety
- キルスイッチの重要性、段階的デプロイ方針

### 3. スケーリング予測

- Gartner「2028年にアプリの33%がエージェントAI搭載」（2024年プレスリリース）→ 「40%」は別出典の可能性。要確認
- 「2029年に70%がIT運用にエージェントAI」→ ⚠️ 正確出典未確認
- NHI 450億 → CyberArk「NHI:人間ID = 45:1」は実在。総数の出典は未特定

---

## 第18章：エージェントエコシステムの未来

### 1. プロトコル標準化 【確度: 高】

- **MCP**: Anthropic 2024年11月。ツール/データ接続。Cursor, Zed, Replit等採用
- **A2A**: Google 2025年4月。エージェント間通信。50+社参加
- **OpenAI Agents SDK**: 2025年3月。独自ハンドオフプロトコル
- 関係性: MCP（ツール接続）+ A2A（エージェント間）= 補完的

### 2. DID/分散型ガバナンス 【確度: 低〜中】

- W3C DID仕様: 2022年7月 Recommendation化
- AIエージェント×DID: 議論段階。成熟した実装標準なし
- Fetch.ai: 分散型AIエージェント、ブロックチェーン取引記録
- SingularityNET: AIサービスマーケットプレイス

### 3. MCPマーケットプレイス 【確度: 中〜高】

- 公式MCPサーバー一覧: https://github.com/modelcontextprotocol/servers
- Smithery.ai: コミュニティMCPサーバーディレクトリ
- mcp.run: MCPサーバーホスティング
- Glama.ai: MCPサーバーディレクトリ
- **セキュリティレビュー**: 公式リポジトリはAnthropicレビュー済み。コミュニティサーバーは体系的レビュー**未整備**
- Invariant Labs MCP Scanner: 自動脆弱性スキャン

---

## 全体の要検証リスト（Web検索で補完必須）

### カットオフ後の情報（2025年6月以降）
- [ ] OpenClaw危機の実在確認
- [ ] LiteLLM 300GB流出の詳細
- [ ] NIST AI Agent Standards Initiative (2026年2月)
- [ ] Oxford Legal Alignment論文 (2026年1月)
- [ ] A2A Linux Foundation移管 (2025年6月)

### 出典未特定の数値
- [ ] Adversa AI 35%/10万ドル
- [ ] Barracuda 43種フレームワーク脆弱性
- [ ] California AB 316のAIエージェント版
- [ ] Gartner「40%」「70%」の正確な出典
- [ ] NHI 450億の正確な出典
- [ ] 攻撃成功率81%
- [ ] Sleeper Agents「99.9%」（概念的表現 vs 具体数値）
