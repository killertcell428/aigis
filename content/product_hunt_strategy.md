# Product Hunt ローンチ戦略 — リサーチに基づく最適化

> 作成: 2026-04-06
> 目的: PH リサーチ結果を踏まえた Aigis ローンチ戦略の策定

---

## 1. リサーチで判明した重要事実

### ⚠️ Coming Soon ページは廃止済み（2025年8月〜）

**当初の計画を修正する必要がある。**
PH の「Coming Soon / Teaser」ページは 2025 年 8 月に廃止された。
"Notify Me" ボタンでフォロワーを集める手法はもう使えない。

**代替手段（現在の PH で使える方法）:**
1. **Product Forum（/p/）** — プロダクト専用フォーラムで事前にコミュニティを形成
2. **Product Draft** — ドラフトを早期作成し、Product Hub & Forum にアクセス
3. **Maker 個人アカウントのフォロワー構築** — PH 上で他製品にコメント・upvote して存在感を出す
4. **外部チャネルからの誘導** — Twitter/X、LinkedIn、Reddit で事前に PH ローンチを告知

### アルゴリズムの仕組み（2026年版）

| 要素 | 重み | 備考 |
|------|------|------|
| **投票者のアカウント年齢** | 最高 | 6ヶ月以上のアカウントは新規の10倍の重み |
| **コメントの質と量** | 非常に高い | 50 upvotes + 30 comments > 200 upvotes + 5 comments |
| **投票の速度パターン** | 高い | 急なスパイクはレビュー対象。緩やかな上昇が理想 |
| **エンゲージメント** | 高い | ページ滞在時間、再訪問、Maker の返信速度 |
| **生の upvote 数** | 中程度 | 数より質。300-500 で Top 5 可能 |

### 成功に必要な数値ベンチマーク

| 指標 | Top 5 に必要 | #1 に必要 |
|------|-------------|-----------|
| Upvotes | 300-500 | 500+ |
| Comments | 40-70 | 70+ |
| コメント:Upvote 比 | 1:8 | 1:6 |
| 初回1時間の upvotes | 40+ | 50+ |
| サイトトラフィック（当日） | 2,000-5,000 | 5,000+ |
| メール登録 | 50-100 | 1,000-3,000（#1の場合） |

### 最適なローンチタイミング

- **曜日**: 水曜 > 火曜 > 木曜（月曜は混雑、金〜日は低トラフィック）
- **時間**: **12:01 AM PT**（= JST 16:01）に公開 → 24時間ランキングをフル活用
- **推奨日**: **2026年5月13日（水）** に変更（火曜→水曜）

### 成功した類似プロダクトの事例

| プロダクト | カテゴリ | 結果 | 成功要因 |
|-----------|---------|------|---------|
| Aikido Security | DevSecOps / Security | #1 Product of the Day, #1 Dev Tool of Month | セキュリティ×開発者向け。初回ローンチで大勝 |
| Appwrite Sites | OSS / Dev Tool | #1 Day, #1 Week, #1 Month | 強力な OSS コミュニティ。「OSS Vercel代替」のポジショニング |
| next-forge | OSS / Template | #4 Product of the Day → Vercel 買収 | 6.8K GitHub Stars の事前ベース |
| Dub.co | Dev Tool / SaaS | #1（1,085 upvotes, 210 comments） | 12:01 AM PT ローンチ、初回1時間で 150 upvotes |

### やってはいけないこと

- ❌ upvote を直接依頼する（「upvote してください」→ TOS 違反）
- ❌ 新規アカウントからの大量投票（アルゴリズムが検知、ペナルティ）
- ❌ 投票リング・有料投票サービスの利用
- ❌ 同じメッセージを複数 Slack グループに一斉送信
- ❌ コミュニティ参加なしでのローンチ（silent launch）
- ❌ PH と HN を同日にやる（オーディエンス分散）

---

## 2. Aigis のポジショニング戦略

### 差別化軸（PH 上での競合との違い）

Aikido Security が #1 を取った実績があるので、セキュリティ×開発者ツールは PH で受ける。
ただし Aigis は「OSS・ゼロ依存・個人開発」という独自ポジション。

**PH で刺さるメッセージ:**
> "I built this because my security team kept blocking AI tools at work.
> Now there's an open-source fix: pip install, done."

**キーワード戦略:**
- Primary: `Open Source` + `Developer Tools` + `AI`
- Secondary: `Cybersecurity` + `Python`
- PH Topics: `open-source`, `developer-tools`, `artificial-intelligence`, `cybersecurity`

### ターゲット投票者

PH の投票重みを最大化するために、以下の層を優先的に巻き込む:

1. **PH 常連ユーザー**（アカウント 6ヶ月以上）— 重み 10x
2. **開発者コミュニティの知人** — コメントも書いてもらえる
3. **OSS コントリビューター** — 技術的なコメントを書ける
4. **Twitter/X のテック系フォロワー** — 拡散力

**避けるべき:**
- 新規 PH アカウント作成を依頼する（重みが低い + 不自然）
- 非テック系の友人・家族（コメントの質が下がる）

---

## 3. 修正版ローンチ計画

### Phase A: Maker 信頼構築（4/6 〜 4/20）— 2週間

Coming Soon ページが使えないため、**Maker 個人の PH 上での存在感**が代替手段。

**毎日やること（15分/日）:**
- PH で新着プロダクト 2-3 件に upvote + 質のあるコメントを残す
- 特に `Developer Tools`, `Open Source`, `AI`, `Cybersecurity` カテゴリ
- コメントは「使ってみた感想」「技術的な質問」「改善提案」など具体的に

**週次やること:**
- PH Discussions に 1 件投稿（質問 or 知見共有）
  - 例: "What's the best approach to scanning LLM inputs for prompt injection?"
  - 例: "How do you handle security governance for AI agents in your org?"
- 他の Maker のローンチにコメントで応援

**目標:**
- PH プロフィールに 20+ のコメント履歴
- 5+ の Maker とのリレーション構築
- フォロワー 10-20 人

### Phase B: 外部コミュニティ種まき（4/14 〜 4/28）— 2週間

**Twitter/X:**
- PH ローンチを予告するツイート（「5月に Product Hunt でローンチします」）
- 技術的な tweet を週 3-5 本（AI セキュリティ tips、プロンプトインジェクション事例）
- PH 常連ユーザーのツイートにリプライ・RT

**Reddit:**
- r/Python, r/MachineLearning で質問に回答（Aigis を自然に紹介）
- r/SideProject で進捗共有

**Zenn/Qiita:**
- PH ローンチ前に 2-3 本の技術記事を投稿
- 記事末尾に「PH でもローンチ予定」と軽く告知

**目標:**
- 支援者リスト 50-100 名（PH アカウント 6ヶ月以上の人を優先）
- Twitter フォロワー +50

### Phase C: ローンチ準備（4/28 〜 5/12）— 2週間

**PH ドラフト作成:**
- Product Draft を PH に作成（ギャラリー画像・コピー・カテゴリ設定）
- Maker Comment を最終確認

**支援者への事前連絡:**
- 「フィードバックをいただけると嬉しいです」（upvote 依頼ではなく feedback 依頼）
- PH ページの URL を事前共有（ドラフト URL or 当日 URL の見込み）
- タイムゾーン別に連絡時間をずらす

**アセット最終化:**
- ギャラリー画像 5 枚
- デモ動画 or GIF
- OG image PNG
- LP の最終チェック

### Phase D: ローンチ当日（5/13 水曜）

**修正版タイムライン（水曜日）:**

| 時間 (JST) | 時間 (PT) | アクション |
|------------|-----------|----------|
| 16:01 | 00:01 AM | PH listing 公開。即座に Maker Comment 投稿 |
| 16:15 | 00:15 AM | 第1波: 最も信頼できる支援者 20-30名に DM（PT 深夜なので US 圏は翌朝） |
| 17:00 | 01:00 AM | Twitter/X で告知（日本の夕方 = 高エンゲージ時間帯） |
| 18:00 | 02:00 AM | LinkedIn 投稿 |
| 22:00 | 06:00 AM | 第2波: US 東海岸が起床。支援者への 2nd DM |
| 翌 01:00 | 09:00 AM | 第3波: US 西海岸が起床。Reddit, DEV.to, Discord 投稿 |
| 翌 04:00 | 12:00 PM | 中間プッシュ。進捗ツイート |
| 翌 07:00 | 03:00 PM | US 午後。最終プッシュ |
| 翌 10:00 | 06:00 PM | Zenn/Qiita 投稿（日本翌朝） |
| 翌 16:00 | 00:00 AM | ランキング確定。結果ツイート |

**全日やること:**
- PH コメントに**全て 30 分以内**に返信
- 進捗ツイートを 3-4 時間ごと
- 投票の流入を自然に分散させる（一気に来ないよう段階的に連絡）

### Phase E: ポストローンチ（5/14〜）

- 結果まとめツイート + Zenn 振り返り記事
- PH で繋がった人にフォローアップ
- HN クロスポスト（PH 翌日に）
- 新規 Stars / DL / メール登録を計測

---

## 4. リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| GitHub Stars が少ない（現在 4） | Social proof 不足 | ローンチ前に Stars 50+ を目指す。Zenn/Qiita 記事から誘導 |
| 支援者が集まらない | 初回1時間の velocity 不足 | 最低 50 名のコミットメント。足りなければローンチ延期も検討 |
| 同日に強力な競合がローンチ | Top 5 入りが困難に | 前日に PH をチェック。強すぎる相手がいたら1日ずらす |
| コメントが技術的すぎて一般ユーザーに刺さらない | エンゲージメント低下 | Maker Comment を「ストーリー」中心に。技術詳細はスレッドで |
| アルゴリズムがスパム判定 | 順位急落 | 投票依頼を絶対しない。分散的・自然な流入を維持 |

---

## 5. 成功/撤退基準

### Go 判断（5/5 時点で確認）
- [ ] PH プロフィールに 20+ コメント履歴がある
- [ ] 支援者リスト 50+ 名（うち PH 6ヶ月以上アカウント 30+）
- [ ] GitHub Stars 30+
- [ ] ギャラリー画像・デモ動画が完成している
- [ ] LP が正常動作し OG image が表示される

**全て満たせばローンチ実行。2つ以上未達なら 5/20 or 5/27 に延期。**

### 成功基準（当日）
| レベル | Upvotes | Comments | 新規 Stars |
|--------|---------|----------|-----------|
| Minimum | 100 | 20 | +30 |
| Good | 300 | 50 | +100 |
| Great | 500+ | 70+ | +300 |

---

Sources:
- [Product Hunt Launch Checklist: Get Top 5 (2026 Guide)](https://www.vibrantsnap.com/blog/product-hunt-launch-checklist-top-5)
- [Product Hunt Launch Playbook: The Definitive Guide (2026 Edition)](https://dev.to/iris1031/product-hunt-launch-playbook-the-definitive-guide-30x-1-winner-1pbh)
- [How would I approach Product Hunt in 2026?](https://www.producthunt.com/p/producthunt/how-would-i-approach-product-hunt-in-2026)
- [Product Hunt Launch Guide: Insights From 15+ Successful Launches](https://launchpedia.co/product-hunt-launch-guide/)
- [How to launch a developer tool on Product Hunt in 2026](https://hackmamba.io/developer-marketing/how-to-launch-on-product-hunt/)
- [How can you promote your launch when "Coming soon" is no longer available?](https://www.producthunt.com/p/producthunt/how-can-you-promote-your-launch-when-the-coming-soon-page-is-not-longer-available)
- [Product Hunt Launch Playbook: How To Become #1 in 2025](https://arc.dev/employer-blog/product-hunt-launch-playbook/)
- [Best of Product Hunt: 2025](https://www.producthunt.com/leaderboard/yearly/2025/all)
