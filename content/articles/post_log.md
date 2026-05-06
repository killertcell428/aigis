# Aigis コンテンツマーケティング — 投稿ログ

## 2026-05-06 (Zenn リライト：5/3 Qiita ヒット記事の再ヒット狙い)

### Zenn 記事
- **テーマ**: 「情シスに『AIエージェントのセキュリティどうするの？』と聞かれたときの設計レベルの答え方」
- **ファイル**: `articles/ai-agent-security-design-answer.md`
- **トピック**: ai, セキュリティ, llm, ガバナンス, Python
- **ステータス**: 下書き完了（published: false）— ユーザーレビュー後に published: true で push
- **文字数**: 約 11,400 字
- **タイトル字数**: 40字

### 選定理由
- **5/3 Qiita ヒット（65 likes / 62 stocks）の Zenn 横展開** が週次レポート §5 の最優先アクション
- content_insights タイトル形式仮説の3条件を満たす: 40字（30〜45字に収まる）／問いかけ形（「〜と聞かれたとき」）／主語明示（「情シス」）
- Comment and Control 自動同期で Zenn 0/0 だった反省を踏まえ、**自動同期せず Zenn 用に手動リライト**

### Qiita 5/3 版との差別化（Zenn 受け要素にシフト）
- **トラスト境界の解剖図**（既存セキュリティ製品 vs AIが新たに作る①入口/②出口/③道具）を冒頭に追加
- 各 Q ブロックに **「設計原則」** ボックスを追加し「なぜこの設計か」を厚く説明
  - Q1: 監査ログは「改ざん不能な数珠つなぎ」で持つ（ハッシュチェーン図解）
  - Q2: 「壁の特性を直交させる」+ 「言葉の中身で止める」から「データの出自で止める」への CaMeL 方式設計転換
  - Q3: 「規制対応はテンプレート × ハッシュチェーンログで事前マッピング」
- **規制マッピング表（4ヶ国44種）は短縮**して、「なぜテンプレート方式か」の設計理由ブロックに置き換え
- 末尾の「やらないこと」「要点サマリ」は維持（信頼性ブースト要素）
- 関連記事リンクで 3/28 Zenn 旧版・5/3 Qiita 版へのクロスリンクを追加

### 公開オペレーション
- `articles/ai-agent-security-design-answer.md` に `published: false` で配置済み
- 公開時はホスト側 PowerShell で frontmatter を `published: true` に変更 → `git push origin master`
- Zenn は GitHub 連携で `articles/**` の `published: true` を検知して自動公開
- **今回は意図的に Qiita へ自動同期しない**（5/3 Qiita 既存記事と内容が一部重複するため）。手動同期したい場合は `articles/{slug}_qiita.md` 名で別ファイル化

---

## 2026-05-02 (LiteLLM CVE-2026-42208 / 議事録 AI 訴訟 — 週次自動ストック)

### Qiita 記事（aigis / AI ゲートウェイ）
- **テーマ**: 「LiteLLM の脆弱性、開示 36 時間で攻撃来てるって本当？」と聞かれたときに見せる、AI ゲートウェイ前段 3 行ガード
- **ファイル**: `2026-05-02_litellm_cve42208_qiita.md`
- **タグ**: Security, AI, Python, LLM, LiteLLM
- **ステータス**: 下書き完了（private: false）— 自動投稿未実施
- **投稿先 URL**: https://qiita.com/drafts/new

### Zenn 記事（Helm / 議事録 AI プライバシー）
- **テーマ**: 「Otter.ai が会議終了後も録音してた件、議事録 AI ってもう使えないの？」と聞かれたときの答え方
- **ファイル**: `2026-05-02_meeting_ai_privacy_zenn.md`
- **トピック**: ai, security, privacy, saas, meeting
- **ステータス**: 下書き完了（published: false）— 自動投稿未実施
- **投稿先 URL**: https://zenn.dev/dashboard

### 選定理由
- content_insights.md の再現ヒット型「**〜と聞かれたときに見せる/答え方〜**」（Zenn 3/28: 116 likes / 91 bookmarks 実績）を 2 本とも踏襲
- 2026-04-24 開示 / 26-27 in-the-wild の **CVE-2026-42208 LiteLLM Pre-Auth SQLi (CVSS 9.3)** を主軸に、**AI ゲートウェイ層が過去最速で攻撃される**ナラティブを構築（LMDeploy 12-13h / LiteLLM 36h の対比）
- Helm 側は **5/20 Otter.ai motion-to-dismiss 聴聞 / Fireflies BIPA 訴訟** という時事性に EU AI Act Article 12 の 8/2 期限（残り 3 ヶ月）を組み合わせ、「議事録 AI もう使えないの？」を引き受ける構成
- 4/29 (Comment and Control) と**攻撃面が重複しない**（今回は AI ゲートウェイ層 / 議事録 AI プライバシー）
- 失敗型回避: 「巨人比較」「長文規制チェックリスト」を避け、**具体脅威**と**今日やる 3 つ**にフォーカス
- 両記事末尾に「5 分で試せるクイックスタート（pip install pyaigis → 3 行）」を配置

### Qiita / Zenn 角度の差別化
- Qiita 版（aigis）: **PoC 中心・How-to 寄り**。IoC grep / WAF Nginx・Caddy・Traefik の 3 行ルール / aigis を LiteLLM 前段に挟む FastAPI 最小例
- Zenn 版（Helm）: **設計欠陥の分解寄り**。3 つの軸（録音停止・voiceprint・データ所在）→ 設計原則 → ベンダ選定 5 質問 → Article 12 ログ最小実装

### ソース
- The Hacker News, *LiteLLM CVE-2026-42208 SQL Injection Exploited within 36 Hours of Disclosure* (2026-04-29)
- Sysdig Blog, *CVE-2026-42208* / *CVE-2026-33626 LMDeploy SSRF*
- LiteLLM Docs, *Security Update: CVE-2026-42208 in LiteLLM Proxy* (v1.83.7)
- UC Today, *Otter.ai Lawsuit: AI Meeting Bot 'Kept Listening' After Call Ended*
- Workplace Privacy Report, *AI Meeting Assistants and Biometric Privacy: Governance Lessons from the Fireflies.AI Lawsuit*
- Help Net Security (2026-04-16), *What the EU AI Act requires for AI agent logging*
- EU AI Act, *Article 12: Record-Keeping for High-Risk AI Systems*

### 関連週次レポート
- `weekly/2026-05-02_weekly_trends.md`（同日生成）

---

## 2026-04-22 (MCP STDIO 脆弱性 / OX Security 開示)

### Zenn記事
- **テーマ**: 「MCPの150M DL脆弱性、うちは大丈夫？」と聞かれたときに見せるSTDIO transport解剖
- **ファイル**: `20260422_mcp_stdio_disclosure_zenn.md`
- **トピック**: ai, security, mcp, claude, anthropic
- **ステータス**: 下書き完了（published: false）— 自動投稿未実施（Chrome MCP 経由の手動投稿が必要）
- **投稿先URL**: https://zenn.dev/dashboard

### Qiita記事
- **テーマ**: 「MCPの150M DL脆弱性、対策は利用者側って本当？」と聞かれたときに見せる 30 分サプライチェーン点検手順
- **ファイル**: `20260422_mcp_stdio_disclosure_qiita.md`
- **タグ**: Security, AI, Python, AIエージェント, MCPサーバー
- **ステータス**: 下書き完了 — 自動投稿未実施（Chrome MCP 経由の手動投稿が必要）
- **投稿先URL**: https://qiita.com/drafts/new

### 選定理由
- content_insights.md の再現ヒット型「〜と聞かれたときに見せる〜」（Zenn 3/28 で 116 likes / 91 bookmarks 実績）を踏襲
- 2026-04-15 OX Security 開示は **Anthropic 公式 SDK 直撃・150M DL 影響・"by design" で unpatched** という強いニュース性
- 4/16 の MCP 記事（Tool Poisoning / Rug Pull / Shadow MCP）と角度が完全に異なる（今回は STDIO transport の構造欠陥 / サプライチェーン）ので **カニバリゼーション回避**
- 失敗型（エンタープライズ巨人との比較）を避け、具体脅威（STDIO RCE）への実用的な答えに集中
- 記事末尾に「5 分で試せるクイックスタート（pip install → 3 行コード）」を両記事に配置

### ソース（研究時）
- OX Security: *The Mother of All AI Supply Chains* / *MCP Supply Chain Advisory*
- The Hacker News / SecurityWeek / Infosecurity Magazine / TechRepublic の 2026-04 記事群
- LiteLLM Security Advisory (CVE-2026-35029 / 35030 / 30623)

---

## 2026-04-10 (Claude Mythos Preview 特集)

### Zenn記事
- **テーマ**: Claude Mythos Previewの衝撃 — 企業AIセキュリティの新パラダイム
- **ファイル**: `claude-mythos-enterprise-security.md` (articles/)
- **トピック**: Claude, AI, セキュリティ, LLM, Anthropic
- **ステータス**: 下書き完了（published: false）

### Qiita記事
- **テーマ**: Claude Mythos時代のAIエージェントセキュリティ — OSSで始める6つの新脅威対策
- **ファイル**: `20260410_mythos_preview_security_qiita.md`
- **タグ**: AI, セキュリティ, Python, Claude, AIエージェント
- **ステータス**: 下書き完了

### Dev.to記事
- **テーマ**: Claude Mythos Preview: 6 New Threat Categories Every AI Security Team Must Address Now
- **ファイル**: `20260410_mythos_preview_security_devto.md`
- **タグ**: ai, security, python, webdev
- **ステータス**: 下書き完了

### aigis v1.2.0 リリースノート
- Mythos-era 6新カテゴリ・28パターン追加
- benchmark corpus 42テストケース追加
- similarity.py 30攻撃フレーズ追加

---

## 2026-04-10

### Qiita記事
- **テーマ**: Cursor 3「エージェントファースト」時代のセキュリティを考える
- **ファイル**: `20260410_cursor3_agent_security_qiita.md`
- **タグ**: AI, セキュリティ, Cursor, MCPサーバー, AIエージェント
- **ステータス**: 未投稿（Chrome未接続のため手動投稿が必要）
- **投稿先URL**: https://qiita.com/drafts/new

### Zenn記事
- **テーマ**: IPA「AIセキュリティ短信 2026年3月号」全項目を読み解く
- **ファイル**: `20260410_ipa_ai_security_bulletin_zenn.md`
- **トピック**: AI, セキュリティ, IPA, LLM, AIエージェント
- **ステータス**: 未投稿（Chrome未接続のため手動投稿が必要）
- **投稿先URL**: https://zenn.dev/dashboard

### 選定理由
- **Cursor 3**（4/2リリース）はエージェントファーストへの大転換であり、開発者の関心が非常に高い。セキュリティ観点での解説記事が少なく差別化可能
- **IPA AIセキュリティ短信**（4/2公開）は情シス向けの公的資料で、全項目解説が日本語でまだ少ない。社内展開に使える実用的価値が高い

---

## 2026-04-06

### Dev.to記事
- **テーマ**: MCP Injection Rate / LangChain Security / LLM Security Tools Comparison / MCP Server Trust Scoring
- **ファイル**: `20260406_mcp_injection_rate_devto.md`, `20260406_langchain_security_devto.md`, `devto_llm_security_tools_comparison_2026.md`, `devto_mcp_server_trust_scoring.md`

## 2026-04-03

### Zenn記事
- **テーマ**: AI事業者ガイドライン v1.2 / Singapore AI Governance
- **ファイル**: `20260406_guideline_v12_compliance.md`, `20260402_singapore_agentic_ai_governance.md`

## 2026-04-01

### Qiita記事
- **テーマ**: AIコーディングエージェントの実践セキュリティガイド
- **ファイル**: `20260401_coding_agent_security_qiita.md`

### Zenn記事
- **テーマ**: エージェント権限障害
- **ファイル**: `20260401_agent_authority_failure_zenn.md`

## 2026-03-30

### 複数記事
- **テーマ**: Claude Code APT / MIC AI Security Guideline / OWASP Agentic Top10 / NHI Claude Code / MCP Rugpull / EchoLeak / A2A Security / AI Memory Poisoning
- **ファイル**: 各種 `20260330_*.md`

## 2026-03-29

### Qiita/Zenn記事
- **テーマ**: MCP Security / MCP Trust Model
- **ファイル**: `20260329_mcp_security_qiita.md`, `20260329_mcp_trust_model_zenn.md`

## 2026-03-28

### 記事
- **テーマ**: Claude Code Full Automation
- **ファイル**: `20260328_claude_code_full_automation.md`

---

## 2026-04-29 (Comment and Control / GitHub PR コメント経由のクレデンシャル流出)

### Qiita 記事
- **テーマ**: 「PR コメントを読ませただけで Claude Code がクレデンシャル吐くって本当？」と聞かれたときに見せる Comment and Control 解剖
- **ファイル**: `20260429_comment_and_control_qiita.md`
- **タグ**: Security, Python, ClaudeCode, AIエージェント, GitHub
- **ステータス**: 下書き完了（published: false）— 自動投稿未実施（Chrome MCP 経由の手動投稿が必要）
- **投稿先 URL**: https://qiita.com/drafts/new

### Zenn 記事
- **テーマ**: 「Claude Code・Gemini・Copilot が PR コメント経由で全部抜かれたらしいけど、何が共通の壊れ方なの？」と聞かれたときの設計レベルの答え方
- **ファイル**: `20260429_comment_and_control_zenn.md`
- **トピック**: security, Python, LLM, AIエージェント, GitHub
- **ステータス**: 下書き完了（published: false）— 自動投稿未実施（Chrome MCP 経由の手動投稿が必要）
- **投稿先 URL**: https://zenn.dev/dashboard

### 選定理由
- content_insights.md の再現ヒット型「**〜と聞かれたときに見せる/答え方〜**」（Zenn 3/28: 116 likes / 91 bookmarks 実績）を踏襲
- 2026-04 Aonan Guan 氏（Johns Hopkins 共同）開示の **Comment and Control** は **CVSS 9.4 Critical**・**3 ベンダー同時影響**・**CI/CD 文脈の確信犯的 Confused Deputy** という強いニュース性
- 4/22 (MCP STDIO supply chain) と 4/18 (社内 RAG IPI) と**攻撃面が重複しない**（今回は GitHub PR コメント / CI runner）
- Google Online Security Blog + Forcepoint X-Labs (2026-04) の "in the wild" 発表で IPI が時事ネタ化しており、**コーディングエージェント運用層**に直接刺さる
- 失敗型（エンタープライズ巨人比較・長文規制チェックリスト）を避け、**具体脅威**（Comment and Control PoC）への実用的な答えに集中
- 記事末尾に「5 分で試せるクイックスタート（pip install pyaigis → 3 行コード → GitHub Actions 最小例）」を両記事に配置

### Qiita / Zenn 角度の差別化
- Qiita 版: **PoC 中心・How-to 寄り**。3 ベンダー個別の最小再現ペイロード→ 3 層防御の実装→ aigis を CI に挟む `.github/workflows/ai-review.yml` の最小例
- Zenn 版: **設計欠陥の分解寄り**。3 つの共通の壊れ方（文字列トラスト境界 / 入出力同居 / 出力チャネル対称性）→ Confused Deputy としての位置づけ→ 段別比較表→ 設計レベルの再構築

### ソース
- Aonan Guan blog, *Comment and Control: Prompt Injection to Credential Theft in Claude Code, Gemini CLI, and GitHub Copilot Agent* (2026-04)
- SecurityWeek / Cybersecurity News / GBHackers / Cyberpress / VentureBeat / Rewterz の 2026-04 記事群
- Google Online Security Blog (2026-04), Forcepoint X-Labs (2026-04), Help Net Security (2026-04-24)
- OWASP LLM Top 10 2026 — LLM01: Prompt Injection

### 公開オペレーション（2026-04-29 追記）
- 上記 2 本を Zenn frontmatter 形式（`published: true`）で **`articles/`** に配置済み:
  - `articles/20260429_comment_and_control_zenn.md`
  - `articles/20260429_comment_and_control_qiita.md`
- サンドボックスから `git push` できないため、ホスト側 PowerShell で `git push origin master` を実行する必要あり（手順は `content/articles/PUSH_INSTRUCTIONS_20260429.md` 参照）
- push 後の自動フロー:
  1. `sync-zenn-qiita.yml` が `articles/**` を検知 → `scripts/sync_zenn_to_qiita.py` 実行 → `public/20260429_comment_and_control_*.md` 自動生成
  2. `publish.yml` が `public/**` を検知 → `increments/qiita-cli/actions/publish@v1` で Qiita 公開
  3. Zenn は GitHub 連携で `articles/**` の `published: true` を検知して自動公開
- 結果: Zenn 2 本 + Qiita 2 本（Zenn 版＋Qiita 版、ユーザー指示に従い両方公開）
- 補足: GitHub MCP は OAuth 開始時に "Incompatible auth server: does not support dynamic client registration" で失敗。`/mcp` での手動認証 or 上記 PowerShell 手順での push が必要

---

## 2026-05-06 (CrewAI 4 CVE Chain / Code Interpreter サンドボックス脱出 — 隔週水曜自動ストック)

### Qiita 記事（aigis / Code Interpreter ガード）
- **テーマ**: 「CrewAI のプロンプト注入で RCE まで通るって本当？」と聞かれたときに見せる、4 CVE 連鎖の最小再現と利用者側 3 行ガード
- **ファイル**: `20260506_crewai_chain_qiita.md`
- **タグ**: Security, Python, AIエージェント, CrewAI, LLM
- **ステータス**: 下書き完了（private: false）— 自動投稿未実施（Chrome MCP 経由の手動投稿が必要）
- **投稿先 URL**: https://qiita.com/drafts/new
- **文字数**: 約 8,800 字

### Zenn 記事（aigis / 設計レベルの解剖）
- **テーマ**: 「CrewAI 4 CVE は何が壊れていたのか？」と聞かれたときの設計レベルの答え方 — 4 つのトラスト境界が一斉に崩れた話
- **ファイル**: `20260506_crewai_chain_zenn.md`
- **トピック**: security, ai, crewai, llm, AIエージェント
- **ステータス**: 下書き完了（published: false）— 自動投稿未実施（Chrome MCP 経由の手動投稿が必要）
- **投稿先 URL**: https://zenn.dev/dashboard
- **文字数**: 約 10,400 字

### 選定理由
- content_insights.md の再現ヒット型「**〜と聞かれたときに見せる/答え方〜**」（Zenn 3/28: 116 likes / 91 bookmarks 実績）を 2 本とも踏襲
- **CrewAI 4 CVE**（CVE-2026-2275 / 2285 / 2286 / 2287, Carnegie Mellon CERT VU#221883）は「プロンプト注入 → Code Interpreter Docker フォールバック → ctypes RCE」の連鎖型で、aigis の `authorize_tool()` (CaMeL 分離) が直接答えになる **完璧なポジショニング材料**
- 直近 3 本（5/2 LiteLLM ゲートウェイ / 4/29 Comment and Control GitHub PR / 4/22 MCP STDIO supply chain）と**攻撃面が完全に異なる**（今回は Code Interpreter / Agent Framework）
- 失敗型回避: 「巨人比較」「長文規制チェックリスト」を避け、**具体脅威**（4 CVE 連鎖）と**今日できる 3 行**にフォーカス
- 両記事末尾に「5 分で試せるクイックスタート（pip install pyaigis → check_input 3 行 → authorize_tool 4 行）」を配置
- 4/29 Comment and Control 記事への内部リンクで **「Untrusted データ provenance」シリーズ** として連続性を作る

### Qiita / Zenn 角度の差別化
- Qiita 版: **PoC 中心・How-to 寄り**。4 CVE 各々の最小再現コード → CrewAI Code Interpreter ラッパへの 3 行挿入 → JSON loader / RAG にも同パターン適用
- Zenn 版: **設計欠陥の分解寄り**。4 トラスト境界の 4 連崩壊 → 「沈黙のフォールバック」アンチパターン → CaMeL 原則の 3 コンポーネント → NeMo Guardrails / LLM Guard / Guardrails AI との比較表 → 4 つの実装パターン

### ソース
- Carnegie Mellon CERT, *VU#221883: CrewAI contains multiple vulnerabilities including SSRF, RCE and local file read*
- SecurityWeek (2026-04), *CrewAI Vulnerabilities Expose Devices to Hacking*
- Cyberpress (2026-04), *CrewAI Vulnerabilities Allow Attackers to Bypass Sandboxes and Compromise Systems*
- GBHackers (2026-04), *CrewAI Hit by Critical Vulnerabilities Enabling Sandbox Escape and Host Compromise*
- ThaiCERT (2026-04-02), *Multiple Vulnerabilities in CrewAI Allow Sandbox Escape and Remote Code Execution via Prompt Injection*
- PointGuard AI, *CrewAI Prompt Injection Leads to System Takeover*
- IronPlate.ai (2026-04-07), *Weekly Threat Intel: OpenClaw CVSS 9.9, CrewAI RCE Chain*
- Adversa AI (2026-05), *Top Agentic AI security resources — May 2026*
- OWASP LLM Top 10 2026 — LLM02: Insecure Output Handling / LLM06: Excessive Agency

### 公開オペレーション（2026-05-06 追記）
- 上記 2 本を `articles/` に配置済み（frontmatter は `published: false` / `private: false` のまま）
- 自動投稿は **Chrome MCP 未接続** のため未実施。ホスト側 PowerShell から `git push` → GitHub Actions の `sync-zenn-qiita.yml` + `publish.yml` で自動化される想定（4/29 と同じフロー）
- 隔週水曜（次回: 2026-05-20）に向けた次回テーマ候補:
  1. **OpenClaw 21,639 instances exposed + 341 malicious skills**（marketplace poisoning, CVE-2026-25253 cross-site WebSocket hijacking）
  2. **Vercel × Context.ai OAuth サプライチェーン**（4/19 開示, AI SaaS as enterprise attack vector）
  3. **n8n Ni8mare CVE-2026-21858**（CVSS 10.0, ~100k servers, Form Webhook content-type confusion → RCE）

### 関連週次レポート
- 直前: `2026-05-02 LiteLLM CVE-2026-42208 / 議事録 AI 訴訟`
- 次回: `2026-05-20 OpenClaw 予定`
