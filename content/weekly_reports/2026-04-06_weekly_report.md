# Aigis 週間SNSレポート - 2026-04-06

レポート期間: 2026-03-30（月）〜 2026-04-06（日）

---

## 1. 今週のアクティビティまとめ

| チャネル | 実績 | 目標 | 達成率 |
|---------|------|------|--------|
| X投稿 | 4本 | 3本 | 133% ✅ |
| Qiita記事 | 1本 | — | — |
| Zenn記事 | 1本（下書き） | — | — |
| Zenn本 | マーケティング素材作成済 | — | — |

### X投稿の詳細

| 日付 | タイプ | 内容 | URL |
|------|--------|------|-----|
| 3/30 | 問いかけ型 | AIエージェント導入の壁「セキュリティは？」突破体験共有 | [リンク](https://x.com/Charles_389_no/status/2038439617129836548) |
| 3/31 | 実用Tips型 | aigisの3行導入紹介 | [リンク](https://x.com/Charles_389_no/status/2038815712953892941) |
| 3/31 | Zenn記事紹介 | Zennセキュリティ記事の紹介投稿 | [リンク](https://x.com/Charles_389_no/status/2038890030547222535) |
| 4/1 | デモ型 | v0.4.0リリース告知（Anthropic SDK統合、PII検出強化） | [リンク](https://x.com/Charles_389_no/status/2039165234498449823) |
| 4/3 | 時事ネタ型 | AI事業者ガイドラインv1.1対応マッピング表公開 | [リンク](https://x.com/Charles_389_no/status/2040001087705657484) |

### 記事投稿の詳細

- **Qiita（4/1公開）**: [Claude CodeやCursorを安全に使うために——AIコーディングエージェントの実践セキュリティガイド【2026年Q1版】](https://qiita.com/sharu389no/items/bf624db3a3b47f8e23bc)
  - テーマ: Q1インシデント分析、権限設計、コーディングエージェント実践ガイド
  - タグ: Security, AI, LLM, ClaudeCode, Python
- **Zenn（4/1下書き保存）**: AIエージェントの暴走は「モデルの問題」ではなく「権限の問題」
  - URL: https://zenn.dev/sharu389no/articles/f2d81d194e89db
  - ステータス: ⚠️ 下書きのまま（公開保留中）

### Zenn本マーケティング準備

- 『AIエージェント・セキュリティ＆ガバナンス実践ガイド』の告知投稿案・スレッド形式5投稿案・記事連動投稿3パターン・Zennコミュニティ告知記事ドラフトを作成済
- 投稿スケジュール案も策定済

### 来週の投稿予定（4/4週下書き作成済）

| 日付 | タイプ | テーマ |
|------|--------|--------|
| 4/5 土 21:00 | デモ型 | v0.4.0 リリース告知（再投稿） |
| 4/6 日 21:00 | 実用ヒント型 | Gandalf Challenge 誘導 |
| 4/7 月 22:00 | 時事ネタ型 | AI事業者ガイドライン v1.1 対応 |
| 4/8 火 22:00 | 衝撃事実型 | litellm サプライチェーン攻撃 |
| 4/9 水 22:00 | 個人開発ストーリー型 | Claude Code Auto Mode 補完 |

---

## 2. 反応・エンゲージメント

### Web検索結果

#### X (Twitter)
- **Aigis固有のメンション**: Web検索では、aigis/Aigisプロジェクト固有のRT・メンション・引用は確認できず
- 「Aigis」で検索すると、The Guardian（英新聞）のAI記事、Cyera社の商用Aigis製品、PocketPaw内のGuardian AIなど同名製品がノイズとなり発見が困難
- **対策**: ハッシュタグ `#aig_guardian` やプロジェクト固有のキーワードを今後統一的に使用することを推奨

#### Qiita
- `aigis` での検索結果なし（既存記事はaigisを直接タイトルに含まず、セキュリティ一般記事として投稿されているため）
- 既存4記事（3/28セキュリティ記事、3/28自動化記事、3/29 MCP記事、4/1コーディングエージェント記事）のいいね数・ストック数は検索からは取得不可

#### Zenn
- `sharu389no` での直接検索結果は上位に表示されず
- 既存の70いいね記事（「AIエージェント導入でセキュリティどうするの？」）は引き続きアセットとして有効
- Zenn本の公開はまだ行われていない模様

### 評価

現時点ではSNS上のオーガニックな反応・メンションは限定的。ただし以下のポジティブ要因あり:
1. Zenn記事の70いいね実績は、AIセキュリティ分野での一定の関心を示す
2. 投稿頻度は目標を上回っている（X: 4本/週 vs 目標3本）
3. Zenn本マーケティング素材の事前準備が完了しており、ローンチ時のインパクトを最大化できる体制

---

## 3. トレンド・競合動向

### 🔥 重大な競合動向（今週のハイライト）

#### Microsoft Agent Governance Toolkit（4/2公開）
- **インパクト: 高** — MITライセンスのOSSとして公開
- Python, TypeScript, Rust, Go, .NETの5言語対応、7パッケージ構成
- Agent OS（ステートレスポリシーエンジン）、Agent Mesh、Agent Runtime、Agent SRE、Agent Compliance等を含む
- aigisとの差別化ポイント: Microsoftは大規模エンタープライズ向け、aigisは軽量・3行導入・日本語特化
- 出典: [Microsoft Open Source Blog](https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/)

#### Cisco DefenseClaw（3/23公開）
- MCP tools、プラグイン等のAIエージェントリソースのセキュリティ検査ツール
- 出典: [SiliconANGLE](https://siliconangle.com/2026/03/23/cisco-debuts-new-ai-agent-security-features-open-source-defenseclaw-tool/)

#### Gen Digital「Sage」（3/9公開）
- Claude Code、Cursor/VS Code等のAIエージェントとOS間にインターセプトレイヤーを挿入
- Bashコマンド、URLフェッチ、ファイル書き込み等のツールコールを検査
- **aigisと直接競合する領域あり**
- 出典: [Help Net Security](https://www.helpnetsecurity.com/2026/03/09/open-source-tool-sage-security-layer-ai-agents/)

#### NVIDIA NeMo Guardrails
- LangChain、LangGraph、LlamaIndexとの統合強化
- GPU加速による低レイテンシ性能
- マルチエージェントデプロイメント対応

### 規制動向

#### AI事業者ガイドライン v1.2 改定案（3/12公表）
- **AIエージェント・フィジカルAIの定義を新設**
- 自律実行するAIに対し「人間の判断介在」（HITL）を事実上義務化
- ログ管理体制の整備を要求
- セキュリティテストの実施を推奨
- 出典: [日経クロステック](https://xtech.nikkei.com/atcl/nxt/column/18/00001/11580/), [Uravation](https://uravation.com/media/japan-ai-regulation-guideline-v12-2026/)
- **Aigisにとっての意味**: 規制対応マッピングをv1.2ベースに更新する好機。4/3投稿のv1.1ネタをv1.2にアップデートすべき

#### AIエージェントセキュリティの市場動向
- コーレ社が「AIエージェント攻撃手法と対策一覧（2026年3月版）」で80種類の脅威を公開（[PR Times](https://prtimes.jp/main/html/rd/p/000000084.000037237.html)）
- 企業セキュリティ担当者の53%が生成AIを認証関連の最大リスクと認識
- 45%がAIエージェントをリスク要因として挙げている
- Adversa AIが [Top Agentic AI Security Resources - April 2026](https://adversa.ai/blog/top-agentic-ai-security-resources-april-2026/) を公開

### Guardrails / LangChain エコシステム
- LangChainのガードレール統合が進化（決定論的ガードレール → モデルベースガードレールの2段構成が推奨）
- エンタープライズでのAIガードレール採用が「オプション」から「必須」へ移行中
- 出典: [Security Boulevard - Guardrails Beyond Vibes](https://securityboulevard.com/2026/04/unprompted-2026-guardrails-beyond-vibes/)

---

## 4. 来週への改善提案

### 投稿内容の方向性

1. **Microsoft Agent Governance Toolkit との比較記事/投稿を最優先で作成**
   - 4/2にMicrosoftが大規模OSSツールキットを公開したことは、AIエージェントセキュリティ分野の認知度向上に大きく寄与
   - 「巨人の参入＝市場の正当化」というナラティブで、aigisの存在意義（軽量・日本語特化・3行導入）を際立たせる
   - 推奨切り口: 「Microsoftが7パッケージで解決しようとしていることを、pip install 1行で始められる」

2. **AI事業者ガイドライン v1.2 対応を明確にアピール**
   - 4/3投稿はv1.1ベースだったが、3/12にv1.2改定案が公表済み
   - v1.2ではAIエージェントの定義が新設され、HITLが事実上義務化
   - aigisのREADMEおよび投稿内容をv1.2ベースに更新すべき

3. **Zenn本のローンチを今週中に実施**
   - マーケティング素材は準備済み
   - 競合の動きが活発化している今、タイミングを逃さないことが重要
   - Zenn記事（下書き2本）も同時公開でインパクトを最大化

### タイミングの調整

- 現在の投稿時間帯（JST 21:00-22:00）は適切
- **月〜水 22:00のピークタイム戦略は継続**
- Zenn本ローンチは**平日朝8:00（通勤時間帯）+ 夜22:00（スレッド展開）**の2段構成を推奨

### 新しい切り口の提案

1. **「比較シリーズ」の開始**: aigis vs Microsoft Agent Governance Toolkit vs Sage vs DefenseClaw
2. **「80種の脅威」に対するaigisのカバレッジ表**: コーレ社の80種分類に対してaigisがどこまでカバーしているかのマッピング
3. **実際のインシデント再現デモ**: litellmサプライチェーン攻撃をaigisで防御するデモ動画/GIF

---

## 5. 来週の推奨アクション

### 最優先（Must Do）

- [ ] **Zenn本『AIエージェント・セキュリティ＆ガバナンス実践ガイド』を公開し、準備済みの告知投稿を実行する**
  - メイン告知 → スレッド5本 → 記事連動投稿 のスケジュールに沿って展開
  - 70いいねZenn記事のフォロワーへのリーチを最大化

- [ ] **Zenn下書き記事2本（MCP信頼モデル + 権限設計）を公開する**
  - 3/29のMCP信頼モデル記事はまだ下書きのまま
  - 4/1の権限設計記事も下書きのまま
  - 本のローンチと同時期に公開することで相乗効果を狙う

- [ ] **AI事業者ガイドライン対応をv1.1→v1.2に更新する**
  - READMEのマッピング表を更新
  - v1.2の「AIエージェント定義新設」「HITL義務化」をaigisの訴求ポイントに追加

### 高優先（Should Do）

- [ ] **Microsoft Agent Governance Toolkit との比較投稿を作成（X + Qiita/Zenn記事）**
  - 切り口: 軽量 vs エンタープライズ、日本語対応、導入の容易さ
  - 「Microsoftも参入した＝この分野は本物」のナラティブ

- [ ] **4/4週のX投稿下書き5本を予定通り投稿する**
  - 特に4/8の litellm サプライチェーン攻撃投稿は、Cisco DefenseClaw の動向と絡めると効果的

- [ ] **プロジェクト固有のハッシュタグ `#aig_guardian` の統一使用を開始**
  - 現在「Aigis」の検索ではノイズが多すぎて発見されにくい
  - 全投稿に `#aig_guardian` を追加し、検索性を向上させる

### 推奨（Nice to Have）

- [ ] **Adversa AI の "Top Agentic AI Security Resources - April 2026" リストへの掲載を狙う**
  - aigisのGitHubをAdversa AIに紹介/PR
- [ ] **コーレ社の80種脅威分類に対するaigisカバレッジマッピング表を作成**
- [ ] **Gen Digital「Sage」との機能比較記事を作成（直接競合分析）**

---

## 6. KPI サマリー（先週比）

| 指標 | 先週 (3/23週) | 今週 (3/30週) | 変化 |
|------|-------------|-------------|------|
| X投稿数 | 3本 | 4本+1（Zenn紹介） | ↑ |
| Qiita記事 | 2本 | 1本 | ↓ |
| Zenn記事 | 2本（1本下書き） | 1本（下書き） | → |
| 新規マーケ素材 | — | Zenn本告知素材一式 | ✅ |

### 注目すべき外部環境の変化

- **Microsoft の参入（4/2）**は市場の正当化という意味でポジティブだが、認知競争が激化するリスクもある
- AI事業者ガイドラインv1.2の改定は、**日本市場での差別化要素**（日本語対応・規制マッピング）を強化する絶好の機会
- エンタープライズ向けガードレールツールの増加は、「個人開発者・中小チーム向けの軽量ツール」というaigisのポジショニングを逆に明確にする

---

*レポート生成日: 2026-04-06*
*次回レポート予定: 2026-04-13*
