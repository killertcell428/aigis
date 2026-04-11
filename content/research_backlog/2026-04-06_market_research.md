# AI/LLMセキュリティ市場調査レポート（2026年4月）

> 調査日: 2026-04-06
> 目的: Aigis の機能優先度を決定するための市場・技術トレンド調査

---

## エグゼクティブサマリー

2026年のAIセキュリティ市場は「エージェントAI時代」に突入し、攻撃面が劇的に拡大している。
従来のプロンプトインジェクション対策だけでは不十分で、**MCPツール汚染**、**メモリポイズニング**、
**クロスエージェント攻撃**、**Shadow AI検知**が新たな必須機能となっている。

Aigis の現状（57ルール・入出力フィルタ・LangGraph統合）は基礎として強固だが、
**エージェント時代の攻撃ベクトルへの対応が最大の差別化機会**。

---

## 1. エンタープライズが最も求めている機能（優先度順）

### 🔴 最優先（小規模チームで即実装可能）

#### 1-1. Shadow AI 検知・可視化
- **需要**: 調査によると全AI利用の90%が「Shadow AI」（未承認利用）。77%の社員が社内データをチャットボットに貼り付けている
- **具体的ニーズ**: ネットワークトラフィック・DNS監視で未承認LLM利用を検出、DLP統合
- **Aigis への提案**: 
  - プロキシモード拡張 → 社内のLLM APIコールを透過的に監視
  - 機密データ（PII、社内コード）のLLM送信を検知・ブロック
  - **実装難易度: 中**（既存のプロキシミドルウェアを拡張）

#### 1-2. エージェント間通信セキュリティ（Inter-Agent Security）
- **需要**: OWASP ASI07「Insecure Inter-Agent Communication」が新規カテゴリに
- **具体的ニーズ**: エージェント間のメッセージ検証、権限境界の強制
- **Aigis への提案**:
  - `AgentBoundaryGuard` クラス: エージェント間通信を検査するミドルウェア
  - 信頼レベルに基づくメッセージフィルタリング
  - **実装難易度: 中**（LangGraphアダプタの拡張として自然）

#### 1-3. MCPセキュリティレイヤー
- **需要**: MCP サーバの43%にコマンドインジェクション脆弱性、5%にツールポイズニング攻撃が既に存在
- **具体的ニーズ**: ツール定義の検証、メタデータ汚染検出、OAuth認証フローの保護
- **Aigis への提案**:
  - `MCPGuard` クラス: MCPツール呼び出しの検査・検証
  - ツール定義の署名検証・ハッシュチェック
  - ツール説明文のプロンプトインジェクション検出
  - **実装難易度: 低〜中**（既存パターンマッチング + MCP SDK連携）

### 🟠 高優先（Phase 2-3で実装）

#### 1-4. メモリポイズニング防御
- **需要**: 研究者がGPT-5 mini・Claude Sonnet 4.5に対して90%+の攻撃成功率を達成
- **具体的ニーズ**: エージェントの長期メモリ整合性検証、異常パターン検出
- **Aigis への提案**:
  - メモリ書き込み時のサニタイゼーション
  - メモリ内容の定期的な整合性チェック
  - 信頼ドメイン別のメモリ分離ポリシー
  - **実装難易度: 中〜高**

#### 1-5. RAGポイズニング検出
- **需要**: たった5つの悪意あるドキュメントで90%の確率でAI応答を操作可能（PoisonedRAG研究）
- **具体的ニーズ**: ベクトルDB投入時のドキュメント検証、異常な埋め込みパターン検出
- **Aigis への提案**:
  - `RAGGuard`: ドキュメント投入時の悪意あるコンテンツスキャン
  - 検索結果の一貫性チェック（異常な偏りの検出）
  - **実装難易度: 中**

#### 1-6. コンプライアンスレポート自動生成
- **需要**: Gartner調査で71%のコンプライアンス責任者がAI利用状況の可視性不足を報告
- **具体的ニーズ**: AI事業者GL、ISO27001、NIST AI RMF 対応の監査レポート
- **Aigis への提案**: 既存のROADMAPにPhase 3で計画済み → **Phase 2への前倒しを推奨**

### 🟡 中優先（差別化として価値あり）

#### 1-7. リアルタイム行動モニタリング
- **需要**: ポリシー違反の80%が内部の誤用（悪意ある攻撃ではない）
- **具体的ニーズ**: 異常な利用パターン検出、リスクスコアリング
- **Aigis への提案**: 既存のactivity.pyを拡張 → 異常検知アルゴリズム追加

#### 1-8. マルチモーダルインジェクション検出
- **需要**: 画像内にテキスト命令を隠す攻撃が増加中
- **具体的ニーズ**: 画像・PDF・音声に埋め込まれた命令の検出
- **Aigis への提案**: 将来的な拡張。現時点ではテキストベースに集中が妥当

---

## 2. 新しい攻撃ベクトル（2025年以降）

### 2-1. Second-Order プロンプトインジェクション
低権限エージェントから高権限エージェントへの権限昇格攻撃。
悪意あるリクエストを低権限エージェント経由で高権限エージェントに転送させる。

### 2-2. MCPサンプリング機能の悪用
MCPサーバがクライアント経由でLLM補完をリクエストする「サンプリング」機能を悪用。
Palo Alto Unit42が報告。

### 2-3. Promptware（プロンプトウェア）
ポリモーフィック型のプロンプト群がマルウェアのように振る舞い、LLMを悪用して
悪意ある活動を実行する新しいマルウェアクラス。

### 2-4. RAGポイズニング
PoisonedRAG研究: 5つの精巧なドキュメントでAI応答の90%を操作可能。
ベクトル埋め込みのリバースエンジニアリングで元テキストの漏洩も。

### 2-5. Confused Deputy（混乱した代理人）攻撃
MCPプロキシサーバが第三者APIに接続する際、適切なユーザーコンテキストなしに
特権アクセスで実行される脆弱性。OAuth認証コードの不正取得が可能。

### 2-6. クロスエージェント推論攻撃
複数のエージェントから個別には無害な部分情報を取得し、
組み合わせることで制限された情報を再構成する攻撃。

### 2-7. メモリポイズニング（持続型）
間接的プロンプトインジェクションでエージェントの長期メモリを汚染。
セッション終了後も永続的に偽の信念を維持し、将来のセッションに影響。

### 2-8. RoguePilot型攻撃
GitHub Issueなどのユーザーコンテンツにプロンプトインジェクションを埋め込み、
Codespace起動時にCopilotが自動実行。GITHUB_TOKENの窃取に成功。

---

## 3. 現行ガードレールツールの不満・ギャップ

### 3-1. 過剰防御（Over-defense）問題
- 最新モデルでも精度が60%近くまで低下（ランダム推測レベル）
- トリガーワードへの過剰反応が実用性を損なう
- **Aigis の優位性**: ベンチマーク100%精度・0%偽陽性を既に達成 → これを強くアピールすべき

### 3-2. レイテンシ問題
- Guardrails AIのバリデータはpost-generation実行 → 全生成コスト + リトライコスト
- 複雑なバリデータ（幻覚検出等）は大幅なレイテンシ追加
- **Aigis の優位性**: ゼロ依存・軽量 → レイテンシ比較ベンチマークを公開すべき

### 3-3. 単一ツールでの全カバーは不可能
- 「no single tool handles all failure modes」が業界のコンセンサス
- Defense-in-depth（多層防御）が必須だが、複数ツール統合の複雑さが障壁
- **Aigis への示唆**: 他ツールとの統合ポイントを積極的に提供（LangChain/LlamaIndex/MCP）

### 3-4. エージェント時代への非対応
- 81%のAIエージェントが稼働中だが、14.4%しかセキュリティ承認を受けていない
- 88%の組織がAIエージェントセキュリティインシデントを報告
- 既存ツールの多くはチャットボット前提 → エージェント対応が遅れている

### 3-5. MCP非対応
- MCPプロトコルにはセキュリティポリシー機構が存在しない
- 「MCP protocol doesn't support human-readable, context-aware policy rules」
- ツール定義の検証・署名機構が標準に含まれない

### 3-6. Hub/API依存の摩擦
- Guardrails AI HubはローカルバリデータにもAPIキーが必要 → オフライン利用不可
- **Aigis の優位性**: ゼロ依存・オフライン完全動作

---

## 4. コミュニティの声（Reddit / HN / GitHub）

### Reddit（r/LocalLLaMA, r/MachineLearning, r/netsec）
- **セルフホスティング需要**: ローカルLLMユーザーは外部サービス依存を嫌う → Aigisのゼロ依存は大きな強み
- **実用的な防御手段の不足**: 「理論は多いが、pip installで使える実装が少ない」
- **LLMで LLMを守る矛盾**: 「同じ型のモデルで評価しても同じ方法で突破される」→ ルールベースの方が信頼性が高いという意見

### Hacker News
- **実際のCVE・攻撃事例への高い関心**: GitHub Copilot CVE-2025-53773（CVSS 9.6）、Cursor CVE（CVSS 9.8）
- **「プロンプトインジェクションはSQLインジェクションのパラメータ化クエリに相当する解決策がない」** という認識
- **Promptware概念の議論**: 新しいマルウェアクラスとしての認知拡大

### GitHub Issues
- **NeMo Guardrails**: 設定の複雑さ、NVIDIA依存への不満
- **Guardrails AI**: Hub APIキー強制、バリデータのレイテンシ
- **PIGuard**: Over-defense問題への対処（MOF戦略）
- **共通要望**: MCP対応、エージェント対応、レイテンシ削減

---

## 5. Gartner/Forrester AI TRiSM 推奨事項

### Gartnerの4層フレームワーク
1. **AI Governance（ガバナンス）**: ポリシー定義・組織横断の管理体制
2. **AI Runtime Inspection & Enforcement（ランタイム検査・強制）**: リアルタイム監視・ポリシー適用
3. **Information Governance（情報ガバナンス）**: データ分類・保護・DLP
4. **Infrastructure & Stack（インフラ）**: 基盤レベルのセキュリティ

### 重要統計
- **2026年末までに、未承認AIトランザクションの80%以上が内部のポリシー違反（悪意ある攻撃ではない）が原因**
- 企業の最大懸念: データ漏洩、サードパーティリスク、不正確/望ましくない出力
- 成熟したAIガバナンスモデルを持つ組織はわずか20%

### Aigis への示唆
- **ポリシーテンプレート（既に実装済み）はGartner推奨に合致** → マーケティングで強調
- **ランタイム検査は最もプロダクトとして差別化しやすい層**
- **コンプライアンスレポート自動生成は企業購買の決め手になりやすい**

---

## 6. MCP セキュリティの新展開

### 判明している脆弱性統計
| 脆弱性タイプ | 影響範囲 |
|-------------|---------|
| コマンドインジェクション | MCPサーバの43% |
| 無制限ネットワークアクセス | 33% |
| ファイルシステム露出 | 22% |
| ツールポイズニング（既に攻撃済み） | 5% |
| OAuth認証フロー脆弱性 | 43% |

### 実際のCVE
- **CVE-2025-68145, CVE-2025-68143, CVE-2025-68144**: AnthropicのGit MCPサーバのRCE脆弱性
- パス検証バイパス、無制限git_init、引数インジェクション

### 実世界のインシデント
- **Supabase/Cursor事件**: サポートチケットに埋め込まれたSQL命令で、特権サービスロールのCursorエージェントが機密トークンを窃取

### Aigis への具体的機会
1. **MCPツール定義スキャナー**: ツールのdescriptionやパラメータにインジェクションが含まれていないか検査
2. **MCPサーバ信頼性スコア**: 署名・バージョン固定・権限範囲に基づくスコアリング
3. **MCPプロキシガード**: MCPクライアント・サーバ間に挿入するセキュリティプロキシ
4. **Rug Pull検出**: ツール定義の動的変更（承認後の悪意ある変更）を検出

---

## 7. Aigis への提案: 優先実装リスト

### 即実装（1-2週間）— Phase 1に組み込み

| # | 機能 | 理由 | 難易度 |
|---|------|------|--------|
| 1 | **MCPツール定義スキャナー** | MCP脆弱性が最もホットな話題。43%の脆弱率は衝撃的。記事ネタにもなる | 低 |
| 2 | **Second-Order インジェクション検出パターン** | 既存パターンエンジンの拡張として自然。新しい攻撃ベクトルへの対応をアピール | 低 |
| 3 | **レイテンシベンチマーク公開** | 競合との差別化。ゼロ依存の速度優位性を数字で証明 | 低 |
| 4 | **Base64/Unicode/Emoji難読化検出** | エージェントセキュリティで必須。既存フィルタの拡張 | 低 |

### 短期（1-2ヶ月）— Phase 1後半〜Phase 2

| # | 機能 | 理由 | 難易度 |
|---|------|------|--------|
| 5 | **MCPプロキシガード** | MCP全体のセキュリティレイヤー。唯一の本格的OSS実装になれる | 中 |
| 6 | **エージェント間通信ガード** | OWASP ASI07対応。LangGraph統合の自然な拡張 | 中 |
| 7 | **メモリポイズニング検出** | 90%+攻撃成功率は企業にとって恐怖。防御策の需要大 | 中 |
| 8 | **RAGドキュメントスキャナー** | RAGは最も普及しているLLM活用パターン。5文書で90%操作可能は衝撃的 | 中 |

### 中期（3-6ヶ月）— Phase 2-3

| # | 機能 | 理由 | 難易度 |
|---|------|------|--------|
| 9 | **Shadow AI検知プロキシ** | エンタープライズ最大の課題。SaaS化との親和性高い | 高 |
| 10 | **コンプライアンスレポート自動生成** | Gartner推奨。企業購買の決め手 | 中 |
| 11 | **Unified Agentic Defense Platform (UADP)** | SACR提唱のフレームワーク。包括的エージェントセキュリティ | 高 |
| 12 | **マルチモーダルインジェクション検出** | 将来の差別化。現時点では優先度低 | 高 |

---

## 8. マーケティング示唆

### 記事ネタ（即座に書ける）
1. 「MCPサーバの43%に脆弱性 — Aigisで守る方法」
2. 「5つのドキュメントでRAGを乗っ取る — PoisonedRAG攻撃と防御」
3. 「メモリポイズニング: AIエージェントの記憶を汚染する新型攻撃」
4. 「OWASP Agentic AI Top 10 — 2026年に知るべき10の脅威」
5. 「Shadow AI: あなたの会社の90%のAI利用は管理外」

### Product Huntでの訴求ポイント
- **「唯一のMCP対応OSSセキュリティツール」** （MCPスキャナー実装後）
- **「ゼロ依存・100%精度・0%偽陽性」** （既存の強み）
- **「エージェント時代のセキュリティ層」** （エージェント間通信ガード実装後）

---

## Sources

- [Top 10 AI Security Tools for Enterprises in 2026 - Reco](https://www.reco.ai/compare/ai-security-tools-for-enterprises)
- [Best AI Security Solutions 2026 - AI News](https://www.artificialintelligence-news.com/news/best-ai-security-solutions-2026-top-enterprise-platforms-compared/)
- [Secure Agentic AI End-to-End - Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/03/20/secure-agentic-ai-end-to-end/)
- [LLM Security Risks in 2026 - Sombra](https://sombrainc.com/blog/llm-security-risks-2026)
- [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [From Prompt Injections to Protocol Exploits - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2405959525001997)
- [New Prompt Injection Attack Vectors Through MCP Sampling - Unit42](https://unit42.paloaltonetworks.com/model-context-protocol-attack-vectors/)
- [MCP Security Vulnerabilities - Practical DevSecOps](https://www.practical-devsecops.com/mcp-security-vulnerabilities/)
- [AI Agent Security 2026: OWASP Top 10 - SwarmSignal](https://swarmsignal.net/ai-agent-security-2026/)
- [Agentic AI Security Threats - Adversa AI](https://adversa.ai/blog/top-agentic-ai-security-resources-april-2026/)
- [OpenAI Guardrails Bypass - HiddenLayer](https://www.hiddenlayer.com/research/same-model-different-hat)
- [PIGuard: Prompt Injection Guardrail via Mitigating Overdefense](https://injecguard.github.io/)
- [AI Guardrails Guide 2026 - Openlayer](https://www.openlayer.com/blog/post/ai-guardrails-llm-guide)
- [AI Guardrails & Output Validation 2026 - ToolHalla](https://toolhalla.ai/blog/ai-agent-guardrails-io-validation-2026)
- [Gartner AI TRiSM Market Guide](https://www.gartner.com/en/documents/6185655)
- [Gartner AI TRiSM Market Guide - Mindgard](https://mindgard.ai/blog/gartner-ai-trism-market-guide)
- [AI TRiSM Framework Guide - AvePoint](https://www.avepoint.com/blog/protect/ai-trism-framework-by-gartner-guide)
- [Shadow AI Detection Tools 2026 - Knostic](https://www.knostic.ai/blog/shadow-ai-detection-tools)
- [Shadow AI Risks and Tools 2026 - Lasso](https://www.lasso.security/blog/what-is-shadow-ai)
- [Google Gemini Prompt Injection Flaw - TheHackerNews](https://thehackernews.com/2026/01/google-gemini-prompt-injection-flaw.html)
- [RoguePilot Flaw in GitHub Codespaces - TheHackerNews](https://thehackernews.com/2026/02/roguepilot-flaw-in-github-codespaces.html)
- [MCP Security Best Practices - Official Spec](https://modelcontextprotocol.io/specification/draft/basic/security_best_practices)
- [Elastic Security Labs - MCP Tools Attack & Defense](https://www.elastic.co/security-labs/mcp-tools-attack-defense-recommendations)
- [Open, Closed and Broken: Prompt Fuzzing - Unit42](https://unit42.paloaltonetworks.com/genai-llm-prompt-fuzzing/)
- [Prompt Injection Attacks 2026 - Astra](https://www.getastra.com/blog/ai-security/prompt-injection-attacks/)
