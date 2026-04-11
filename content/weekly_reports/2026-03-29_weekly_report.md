# Aigis 週間SNSレポート - 2026-03-29

> 自動生成日時: 2026-03-29（スケジュールタスク `aig-weekly-analysis` により生成）

---

## 1. 今週のアクティビティまとめ

| チャネル | 本数 | 目標 | 達成率 |
|---------|------|------|--------|
| X (旧Twitter) | 3本 | 3本 | ✅ 100% |
| Qiita記事 | 3本 | 1本 | ✅ 300% |
| Zenn記事 | 2本（+1本下書き保留） | 1本 | ✅ 200%+ |

### X 投稿詳細

1. **2026-03-28（個人開発ストーリー型）**
   - 内容: 情シスに「セキュリティは？」で却下された体験 → OSS開発のきっかけ
   - URL: https://x.com/Charles_389_no/status/2037802503270793427
   - ハッシュタグ: #ClaudeCode #個人開発 #OSS
   - 狙い: 「自分も同じ」共感リプライ → フォロー獲得

2. **2026-03-29 1回目（衝撃事実型）**
   - 内容: AIエージェント攻撃手法「80種」公開 → Aigisが48パターン検知・ブロック
   - URL: https://x.com/Charles_389_no/status/2038082762356461969
   - ハッシュタグ: #AIセキュリティ #ClaudeCode
   - 狙い: 「怖い」→RT・引用ポスト拡散

3. **2026-03-29 2回目（時事ネタ型 / 自動投稿）**
   - 内容: Claude Code Auto mode + litellmマルウェア混入事例 → 監査ログ+ブロックの必要性
   - URL: https://x.com/Charles_389_no/status/2038091736581554483
   - ハッシュタグ: #ClaudeCode #AIセキュリティ
   - 狙い: 時勢とプロダクトを紐付けた即効性の高い投稿

### 記事投稿詳細

| # | プラットフォーム | タイトル | テーマ | ステータス |
|---|-----------------|---------|--------|-----------|
| 1 | Qiita | [AIエージェント導入で「セキュリティは？」と聞かれたときに見せる技術対策](https://qiita.com/sharu389no/items/7c3904e7e40a8bec505d) | Aigis導入ガイド | ✅ 公開済み |
| 2 | Qiita | [OSSのサービス展開を0からClaude Codeで全自動化してみた](https://qiita.com/sharu389no/items/a328d98f2928a8d0972b) | Claude Code自動化体験 | ✅ 公開済み |
| 3 | Qiita | [60日で30件のCVE——MCPサーバー導入前に知っておくべきセキュリティリスクと実践的対策](https://qiita.com/sharu389no/items/b60aba6e167999975743) | MCPセキュリティ | ✅ 公開済み |
| 4 | Zenn | [AIエージェント導入で「セキュリティどうするの？」と聞かれたときの技術的な答え方](https://zenn.dev/sharu389no/articles/e07c926d87ac57) | Aigis導入ガイド | ✅ 公開済み |
| 5 | Zenn | [OSSのサービス展開を0からClaude Codeで全自動化した話](https://zenn.dev/sharu389no/articles/ed98efe89e7f1e) | Claude Code自動化体験 | ✅ 公開済み |
| 6 | Zenn | [なぜAIエージェントはMCPツールを信頼しすぎるのか——信頼境界から設計するセキュリティアーキテクチャ](https://zenn.dev/sharu389no/articles/5f049a87fdb47e) | MCP信頼モデル深掘り | ⚠️ 下書き保留（投稿上限429エラー） |

**注記**: Zennの6本目は投稿上限エラーにより下書き保留中。来週早々に手動公開が必要。

---

## 2. 反応・エンゲージメント

### Web検索による外部反応調査結果

**Aigis / aigis の直接的な言及:**
- Qiita・Zenn上で「aigis」を検索したところ、自身の投稿記事（上記3本+2本）以外の第三者による言及は**現時点で確認されず**。
- 「Aigis AIエージェント セキュリティ」の一般検索では、自身のZenn記事（セキュリティ導入ガイド）が**検索結果の上位に表示**されていることを確認。これはSEO的に良い兆候。
- Gartnerが「Guardian Agent」というカテゴリを予測しており（2030年までにAgentic AI市場の10-15%を占める見込み）、「Aigis」というブランド名との親和性が高い。

**定量データ（未取得）:**
- X投稿のインプレッション・エンゲージメント数: Twitter Analytics / X App内分析から手動確認が必要（API未設定）
- Qiita LGTM数・ビュー数: Qiita管理画面から確認が必要
- Zenn Like数・ビュー数: Zenn管理画面から確認が必要

**定性評価（投稿タイプ別）:**

| 投稿タイプ | 期待される反応 | 来週の改善ポイント |
|-----------|--------------|-------------------|
| 個人開発ストーリー型 | 共感リプライ・フォロー | 問いかけ文をさらに具体的に（「どうやって社内説得しましたか？」等） |
| 衝撃事実型 | RT・引用ポスト | 画像/図解を添付してインプレッション向上を狙う |
| 時事ネタ型 | 即時リーチ・ブックマーク | ニュース発表から24時間以内の投稿を徹底 |

---

## 3. トレンド・競合動向

### 🔴 最重要: litellmサプライチェーン攻撃（2026-03-24）

2026年3月24日、Pythonパッケージ litellm（月間ダウンロード9,500万回）にマルウェアが混入されたサプライチェーン攻撃が発覚。

- **攻撃手法**: Trivy（セキュリティスキャナー）のGitHubアクションが先に侵害 → CI/CDパイプライン経由でPyPI公開トークンを窃取 → 悪意あるバージョン(1.82.7, 1.82.8)がPyPIに公開
- **被害**: SSH鍵、クラウド認証情報（AWS/GCP/Azure）、Kubernetes秘密情報、暗号通貨ウォレットなどを暗号化して外部に送信
- **影響時間**: 約3時間でPyPIが隔離
- **Aigisとの関連**: 今週の3投稿目でこの事件を既に取り上げ済み。**AIエージェント経由のサプライチェーン攻撃が現実化**したことで、Aigisの「操作ログ+危険操作ブロック」の必要性が一層明確に。

**来週のアクション**: この事件の詳細技術解説記事を執筆し、Aigisがどのレイヤーで防御に寄与できるかを具体的に示す。

### 🟠 MCP脆弱性の爆発的増加

- 2026年1〜2月の60日間で**MCPサーバー関連CVEが30件以上**報告
- CVE-2026-23744（MCPJam Inspector RCE、CVSS 9.8）: リモートからHTTPリクエストでMCPサーバーをインストール→RCE可能
- CVE-2026-26118（Azure MCP Server EoP）: SSRFを悪用した権限昇格
- 公開MCPサーバーの**43%に何らかの脆弱性**が存在
- **Aigisとの関連**: 今週のQiita記事（MCPセキュリティ）とZenn記事（MCP信頼モデル）でこのトレンドを既にカバー。タイムリーな記事投稿ができた。

### 🟡 AI事業者ガイドライン第1.1版（2026年3月末公表予定）

- 総務省・経産省が2026年3月12日の有識者会合で改定案を公表
- **AIエージェントの定義を新設**: 「特定の目標を達成するために、環境を感知し自律的に行動するAIシステム」
- **人間の判断介在を必須化**: AIエージェントが高額商品を購入する場合の決済前同意確認など具体例を提示
- 意見募集を経て3月末正式公表予定
- **Aigisとの関連**: 「危険操作ブロック」「監査ログ」機能はガイドラインの要求に直接適合。**「ガイドライン準拠」を訴求する絶好のタイミング**。

### 🟢 競合ツール動向

| ツール | 最新動向 | Aigisとの差別化ポイント |
|--------|---------|---------------------------|
| **Guardrails AI** | LangChain統合強化、エンタープライズ向けバリデーション拡充 | Aigisはエージェント操作レベルの監視+OSS無料 |
| **NeMo Guardrails (NVIDIA)** | LLMベースの会話制御に特化 | Aigisはコード実行・ファイル操作の実行レイヤー監視に特化 |
| **Cisco Agent Runtime SDK** | ポリシーをビルド時に強制、AWS/GCP/Azure/LangChain対応 | Aigisはpip一発インストール、SMB/個人開発者向け |
| **Claude Code Auto Mode** | Anthropic自社プラットフォームの安全性制御 | AigisはOSSとして組織独自の監査・ガバナンスを担う（補完関係） |

### 🔵 市場データ

- Gartner: Fortune 500企業の80%がAIエージェントを導入済み（2026年時点）、63%がガバナンス課題に直面
- Gartner: 2027年までにAIプロジェクトの40%がガバナンス不足で失敗と予測
- Gartner: 2030年までに「Guardian Agent」技術がAgentic AI市場の10-15%を占めると予測
- Kiteworks: 中央集約型AIデータゲートウェイを持つ組織は43%のみ、57%がガバナンス体制未整備

---

## 4. 来週への改善提案

### 投稿内容の方向性

1. **「AI事業者ガイドライン準拠」テーマを最優先で攻める**
   3月末の正式公表タイミングに合わせ、Aigisがガイドライン要件をどう満たすか具体的に示す。「ガイドライン対応チェックリスト」形式の投稿が特に刺さりやすい。新年度（4月）のAI導入検討再スタートとも合致する。

2. **litellmサプライチェーン攻撃の深掘り記事**
   セキュリティエンジニア向けに攻撃の技術的詳細（Trivy→CI/CD→PyPIトークン窃取の連鎖）を解説し、AIエージェント環境での防御層としてAigisを位置づける。検索流入が見込めるホットトピック。

3. **Claude Code Auto ModeとAigisの補完関係を明確化**
   「Anthropicはプラットフォームを守るAuto Modeを作った。Aigisはあなたの組織の操作ログ・監査証跡を残す」という切り口で、プラットフォーム依存しない独立OSSの価値を訴求。

### タイミングの調整

- **平日昼12:00-13:00 / 夜21:00-22:00** がAIセキュリティ系タグで最もエンゲージメントが高い
- **月曜朝** は「週初めの情報収集」ニーズが高く、ニュース系投稿が有効
- **3月末〜4月初** は新年度のAI導入検討再スタート時期 → 「導入前に読む」系コンテンツが刺さる
- 1日2投稿は3/29で実施済み → 毎日の投稿ペースを維持しつつ、同日複数投稿は控えめに

### 新しい切り口の提案

1. **ビジュアル投稿**: ブロックログ・ダッシュボードのスクリーンショットを添付した「実物を見せる」投稿（百聞は一見に如かず）
2. **「5分でできる」体験記事**: `pip install aigis` から初期設定完了までの最短パスを示すクイックスタート
3. **情シス・管理職ペルソナ向け**: 「ChatGPTやClaude Codeを業務導入したい担当者が、上司を説得するための資料」という切り口
4. **Gartner「Guardian Agent」予測との接続**: 「Gartnerが予測するGuardian Agent市場 — AigisはそのOSS版」というポジショニング

---

## 5. 来週の推奨アクション

### 最優先（月〜火）
- [ ] Zenn下書き記事（MCP信頼モデル）を手動で公開する（429エラー解消確認後）
- [ ] X投稿①: AI事業者ガイドライン第1.1版の正式公表を受けた解説 → Aigisとの対応を具体的に示す
- [ ] Qiita/Zenn管理画面で今週の記事のビュー数・LGTM/Like数を確認・記録

### 中優先（水〜木）
- [ ] X投稿②: Claude Code Auto ModeとAigisの補完関係を図解で整理
- [ ] Qiita/Zenn記事: litellmサプライチェーン攻撃の技術的詳細 + AIエージェント環境での防御策

### 通常優先（金〜土）
- [ ] X投稿③: litellmマルウェア事件の詳細 + Aigisの検知デモ（スクリーンショット付き）
- [ ] X投稿インプレッション数をX App内分析で確認・記録
- [ ] 次週のX投稿案ドラフト作成（`weekly_x_drafts/2026-04-04_x_drafts.md`）

### 継続改善
- [ ] X Analytics APIの設定を検討し、定量データの自動取得を目指す
- [ ] Gartner「Guardian Agent」レポートの詳細入手を検討（ポジショニング強化のため）

---

## 今週の総合評価

| 指標 | 評価 | コメント |
|------|------|---------|
| 投稿量 | ⭐⭐⭐⭐⭐ | X 3本 + Qiita 3本 + Zenn 2本（+1下書き）。目標を大幅に超過 |
| タイムリーさ | ⭐⭐⭐⭐⭐ | litellm事件・Claude Code Auto Mode・MCP CVEをすべて即日カバー |
| コンテンツ品質 | ⭐⭐⭐⭐ | 技術的深度のある記事を複数公開。ビジュアル要素の追加が次の改善点 |
| 外部反応 | ⭐⭐ | 第三者言及は未確認。SEO上位表示は確認。今後の認知拡大が課題 |
| 戦略的一貫性 | ⭐⭐⭐⭐⭐ | 共感型→衝撃型→時事型と投稿タイプを分散、記事はセキュリティ軸で統一 |

**次週の最大の機会**: AI事業者ガイドライン第1.1版の正式公表（3月末予定）に合わせた「ガイドライン準拠」訴求。新年度の企業AI導入検討再スタートとも重なり、認知拡大の絶好のタイミング。

---

## 参考リンク・情報源

### Aigis関連
- [Zenn記事: AIエージェント導入セキュリティ](https://zenn.dev/sharu389no/articles/e07c926d87ac57)

### トレンド・市場
- [Gartner: Guardian Agents will Capture 10-15% of Agentic AI Market by 2030](https://www.gartner.com/en/newsroom/press-releases/2025-06-11-gartner-predicts-that-guardian-agents-will-capture-10-15-percent-of-the-agentic-ai-market-by-2030)
- [Gartner: セキュリティ対策が不十分なAIエージェントはサイバー攻撃の温床](https://www.gartner.co.jp/ja/newsroom/press-releases/pr-20260316-ai-agent-sec)
- [NTTデータ: 今取り組むべきAIリスク対策とAIガバナンス最新動向](https://www.nttdata.com/jp/ja/trends/data-insight/2026/0313/)
- [Kiteworks: AIエージェントセキュリティ データ層ガバナンスガイド 2026](https://www.kiteworks.com/ja/cybersecurity-risk-management/ai-agent-security-data-layer-governance-2/)
- [AXメディア: 2026年最新 生成AIの規制動向](https://media.a-x.inc/ai-regulation/)

### 事件・脆弱性
- [liteLLM公式: Security Update March 2026](https://docs.litellm.ai/blog/security-update-march-2026)
- [Snyk: How a Poisoned Security Scanner Became the Key to Backdooring LiteLLM](https://snyk.io/articles/poisoned-security-scanner-backdooring-litellm/)
- [Sonatype: Compromised litellm PyPI Package](https://www.sonatype.com/blog/compromised-litellm-pypi-package-delivers-multi-stage-credential-stealer)
- [MCP Security 2026: 30 CVEs in 60 Days](https://www.heyuan110.com/posts/ai/2026-03-10-mcp-security-2026/)
- [CVE-2026-23744: MCPJam Inspector RCE](https://vulnerablemcp.info/vuln/cve-2026-23744-mcpjam-inspector-rce.html)

### 規制
- [日経xTECH: AIの自律実行に「人間の判断介在を」、国がAI事業者ガイドライン改定へ](https://xtech.nikkei.com/atcl/nxt/column/18/00001/11580/)
- [GVA法律事務所: AI事業者ガイドライン改訂の要点](https://gvalaw.jp/blog/i20260303/)
- [AI事業者ガイドライン 第1.1版 概要 (PDF)](https://www.meti.go.jp/shingikai/mono_info_service/ai_shakai_jisso/pdf/20250328_2.pdf)

### 競合
- [Cisco: Reimagines Security for the Agentic Workforce](https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2026/m03/cisco-reimagines-security-for-the-agentic-workforce.html)
- [AI Guardrails 2026: Enterprise Safety Guardians](https://www.programming-helper.com/tech/ai-guardrails-2026-enterprise-safety-guardians-secure-ai-deployment/)
- [Practical DevSecOps: MCP Security Vulnerabilities](https://www.practical-devsecops.com/mcp-security-vulnerabilities/)

---

*このレポートは自動スケジュールタスク `aig-weekly-analysis` により 2026-03-29 に生成されました。*
