# 要検証項目の補完結果

## カットオフ後の情報（全8項目確認済み）

### 1. NIST IR 8596 Cyber AI Profile ✅
- **公開日**: 2025年12月16日（初期公開ドラフト）
- CSF 2.0をAIシステムに適用するプロファイル
- 3つの重点領域: (1) AIシステムのセキュリティ確保 (2) AIを活用したサイバー防御 (3) AI悪用によるサイバー攻撃への対策
- 6,500人以上が開発参加、約1年の開発期間
- ステータス: Preliminary Draft（iprd）。2026年中に正式版予定
- 出典: https://csrc.nist.gov/pubs/ir/8596/iprd
- PDF: https://nvlpubs.nist.gov/nistpubs/ir/2025/NIST.IR.8596.iprd.pdf

### 2. NIST AI Agent Standards Initiative ✅
- **発表日**: 2026年2月17日（NIST CAISI発表）
- AIエージェントの安全な普及・相互運用性の標準化イニシアチブ
- RFI: AIエージェントのセキュリティ（回答期限: 2026年3月9日）
- コンセプトペーパー: エージェントのアイデンティティと認可（回答期限: 2026年4月2日）
- 2026年4月以降セクター別リスニングセッション開催予定
- 出典: https://www.nist.gov/caisi/ai-agent-standards-initiative

### 3. シンガポール Model AI Governance Framework for Agentic AI ✅
- **公開日**: 2026年1月22日（WEF ダボス会議）
- 発行: IMDA、世界初のエージェントAI専用ガバナンスFW、法的拘束力なし（任意）

**4つの柱**:
1. **Assess and Bound Risks Upfront** — 自律度・機微データアクセス・行動範囲を設計段階で制御
2. **Making Humans Meaningfully Accountable** — 開発者・展開者・運用者・エンドユーザーの責任配分。オーバーライド・傍受・レビュー可能な仕組み
3. **Implementing Technical Controls and Processes** — ライフサイクル全体の技術的統制（ベースラインテスト、ホワイトリストアクセス制御等）
4. **Enabling End-User Responsibility** — 透明性確保と教育・トレーニングによる責任ある利用促進

- 出典: https://www.imda.gov.sg/resources/press-releases-factsheets-and-speeches/press-releases/2026/new-model-ai-governance-framework-for-agentic-ai
- PDF: https://www.imda.gov.sg/-/media/imda/files/about/emerging-tech-and-research/artificial-intelligence/mgf-for-agentic-ai.pdf

### 4. AI事業者ガイドライン v1.2 ✅
- **公開日**: 2026年3月31日
- 発行: 総務省・経済産業省
- **エージェント関連の新規追加**:
  - AIエージェントの定義を初めて明記:「環境を感知し、特定の目的達成のために自律的に行動するAIシステム」
  - フィジカルAI（ロボット等）も新たに規制対象
  - HITL（人間の判断介在）の仕組み構築を事実上の必須要件化
  - 具体例: 高額購入前のユーザー同意確認、重要経営判断前の管理者確認
- 出典: https://www.soumu.go.jp/main_content/001059300.pdf

### 5. Microsoft ZT4AI（Zero Trust for AI）✅
- **発表日**: 2026年3月19日（RSAC 2026）
- Zero Trustの原則をAIライフサイクル全体に拡張
- **700以上のセキュリティコントロール**でエージェントAI固有の脆弱性に対応
- 3つの中核原則:
  1. Verify Explicitly — ユーザー・ワークロード・AIエージェントのID+振る舞いを継続的検証
  2. Least Privilege — プロンプト・モデル・プラグイン・データソースへのアクセス制限
  3. Assume Breach — PI・データポイズニング・ラテラルムーブメントへのレジリエンス設計
- リファレンスアーキテクチャ新規公開、Assessment AIピラーは2026年夏予定
- 出典: https://www.microsoft.com/en-us/security/blog/2026/03/19/new-tools-and-guidance-announcing-zero-trust-for-ai/

### 6. Microsoft Agent Governance Toolkit ✅
- **GitHub**: https://github.com/microsoft/agent-governance-toolkit
- **AgentIdentity**: Ed25519暗号鍵、ライフサイクル管理（active/suspended/revoked）
- **SPIFFE/SVID対応**: ゼロトラストエージェントID
- **Trust Score**: 0-1000スケール
- **その他**: ケーパビリティワイルドカード、委任チェーン、JWK/JWKS対応、W3C DID Documentエクスポート
- **OWASP対応**: Agentic Top 10の**10/10をカバー**
- **テスト**: 3言語で6,100以上のテスト

### 7. A2A Linux Foundation移管 ✅
- **発表日**: 2025年6月23日（Open Source Summit North America）
- GoogleがA2A仕様・SDK・開発者ツールをLF寄贈
- **設立メンバー**: AWS, Cisco, Google, Microsoft, Salesforce, SAP, ServiceNow
- ベンダーニュートラルなガバナンス
- 出典: https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents

### 8. A2A参加企業100社超 ✅
- 初期50社超 → LF移管時に100社超に拡大
- テクノロジー: Atlassian, Box, Cohere, MongoDB, PayPal, Microsoft, Zoom, AWS, Cisco
- コンサル: Accenture, BCG, Capgemini, Deloitte, McKinsey, PwC, KPMG等
- 出典: Google Developers Blog + Linux Foundation公式

---

## 出典不明だった統計値・用語（全8項目確認済み）

### 9. PALADIN フレームワーク（5層防御）✅
- **出典**: "Prompt Injection Attacks in LLMs and AI Agent Systems: A Comprehensive Review"
- MDPI *Information*, Vol.17, Issue 1, Article 54
- **発表日**: 2026年1月7日
- URL: https://www.mdpi.com/2078-2489/17/1/54
- 5層defense-in-depthフレームワーク。45件の主要文献を分析したレビュー論文内で提案

### 10. Sentinel Architecture（94%）→ ⚠️ 出典特定不可
- 「94%の攻撃無効化」という数値の正確な出典は未特定
- 関連: Qualifire `prompt-injection-sentinel`（精度0.987, F1=0.980）が存在するが94%とは不一致
- **結論**: 架空統計の可能性あり。本書では使用しない

### 11. LLM-as-Critic +21%精度向上 ✅
- **出典**: "PromptGuard: a structured framework for injection-resilient language models"
- Nature *Scientific Reports*, **2026年1月9日**
- URL: https://www.nature.com/articles/s41598-025-31086-y
- Layer 3（LLM-as-Critic）が単独で**21%の精度向上**。精度87%超、適合率0.89
- フレームワーク全体でインジェクション成功率67%削減、F1=0.91

### 12. 本番AI配備の73%でPI発生 ✅
- **出典**: Cisco "State of AI Security 2026"
- **発表日**: 2026年2月
- URL: https://www.cisco.com/c/en/us/products/security/state-of-ai-security.html
- 監査した本番AIデプロイの**73%**でPI脆弱性発見
- 83%がエージェントAI導入計画、安全に導入できる準備ありは**29%のみ**
- 専用PI防御導入組織は**34.7%のみ**

### 13. 攻撃成功率81%（ベースライン防御比11%）✅
- **出典**: NIST CAISI "Technical Blog: Strengthening AI Agent Hijacking Evaluations"
- **発表日**: 2025年1月17日
- URL: https://www.nist.gov/news-events/news/2025/01/technical-blog-strengthening-ai-agent-hijacking-evaluations
- AgentDojo（ETH Zurich）を使用。最強ベースライン攻撃11% → 新手法で**81%**（7倍改善）
- 対象: Claude 3.5 Sonnet (2024年10月版)。英国AI安全研究所との共同研究
- Workspace環境用攻撃がTravel/Slack/Bankingでも有効

### 14. Adversa AI 35%/10万ドル ✅
- **出典**: Adversa AI "Top AI Security Incidents -- 2025 Edition"
- **発表日**: 2025年7月
- URL: https://www.adversa.ai/top-ai-security-incidents-report-2025-edition/
- プロンプトベース攻撃が全AIセキュリティインシデントの**35.3%**（最多）
- ElizaOS/AiXBT/Chevrolet等で不正暗号通貨送金・偽契約・ブランド毀損、損失**10万ドル超**

### 15. MCPToxベンチマーク ✅
- **出典**: "MCPTox: A Benchmark for Tool Poisoning Attack on Real-World MCP Servers"
- arXiv: https://arxiv.org/abs/2508.14925
- GitHub: https://github.com/zhiqiangwang4/MCPTox-Benchmark
- **発表日**: 2025年8月19日
- 実世界45 MCPサーバー・353ツール、3攻撃テンプレートから1,312テストケース
- 20主要LLMエージェント評価、多くが攻撃成功率60%超、o1-miniは最高**72.8%**
- ⚠️ 「OSSサーバーの5%に既存」はこのベンチマーク自体の主張ではない可能性

### 16. Lethal Trifecta 初出典 ✅
- **初出**: Simon Willison ブログ "The lethal trifecta for AI agents"
- **発表日**: 2025年6月16日
- URL: https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/
- ニュースレター: https://simonw.substack.com/p/the-lethal-trifecta-for-ai-agents（6月17日）
- 3つの危険な組み合わせ:
  1. プライベートデータへのアクセス
  2. 信頼できないコンテンツへの曝露
  3. データ窃取に利用可能な外部通信能力
- Johann Rehbergerがこれに触発され「AI Kill Chain」を提唱、2025年8月「The Month of AI Bugs」でChatGPT/Codex/Cursor/Claude Code等の脆弱性を毎日公開

## カットオフ後インシデント・法規制（補完調査3）

以下は確認不可（Web検索が使えなかった）:
- OpenClaw危機 → 要再調査
- LiteLLM 300GB流出 → 要再調査
- California AB 316 AI版 → 既知は自動運転法案のみ
- MemoryGraft攻撃 → 要再調査
- Gartner 40%/70%の正確出典 → 要再調査
- NHI 450億の正確出典 → NHI:人間=45:1は実在、絶対数は未特定
- Oxford Legal Alignment論文 → 要再調査
- Barracuda 43種脆弱性 → 要再調査
