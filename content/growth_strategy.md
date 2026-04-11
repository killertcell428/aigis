# Aigis グロース戦略 — スター・認知・収益化

## 成功事例から学んだ法則

### ScrapeGraphAI（6ヶ月で1K、次の4ヶ月で10K stars）
- HackerNewsで1投稿 → 数百スター/日
- DEV.toでチュートリアル記事を継続投稿
- Reddit r/programming での定期的なシェア

### Dagu（個人開発で4年→2.3K stars）
- 小粒なイテレーションで動くものを出し続ける
- リリースノートで全貢献者名を明記 → リピート貢献率UP
- 海外ブログに記事掲載 → 大量スター
- はてなブックマークのトレンド入り → 日本での認知

### Guardrails AI（3.5K stars + $7.5M調達）
- 「Hub」で外部コントリビューターがvalidatorを追加できる仕組み
- 月10,000ダウンロード
- 資金調達でメディア露出 → さらにスター増

---

## Aigis専用グロース計画

### Phase 0: 種まき（今すぐ、1-2日）

**目標: 最初の50スター（自分のネットワーク）**

| アクション | チャネル | 期待効果 |
|-----------|---------|---------|
| Twitter/Xで「Gandalfチャレンジ」投稿 | Twitter | ゲーム性でRT狙い |
| Twitter/Xで「2コマンドでAIガバナンス」投稿 | Twitter | エンジニアの共感 |
| 知人・同僚に直接スター依頼 | DM | 最初の20-30スター |
| 自分のQiita/Zennアカウントのプロフィールにリンク | プロフィール | 継続流入 |

### Phase 1: 点火（1週間以内）

**目標: 100-300スター**

| アクション | チャネル | 優先度 | 備考 |
|-----------|---------|--------|------|
| Qiita記事投稿「AIエージェント導入で〜」 | Qiita | 最高 | トレンド入り狙い。火曜/水曜の朝投稿が効果的 |
| Zenn記事投稿「AIエージェント時代の〜」 | Zenn | 最高 | いいね+バッジ狙い |
| はてなブックマークに自分でブクマ | はてブ | 高 | 3ブクマで「新着」に載る |
| Show HN投稿 | HackerNews | 高 | EST朝（日本時間22時頃）に投稿 |
| Reddit r/Python, r/MachineLearning | Reddit | 中 | 英語で投稿 |
| DEV.to英語記事 | DEV.to | 中 | HN投稿の翌日にフォロー |

### Phase 2: 拡大（2-4週間）

**目標: 500-1,000スター**

| アクション | チャネル | 備考 |
|-----------|---------|------|
| 「Gandalf Challenge」のバイラルキャンペーン | Twitter/X | 「全7レベルクリアした人」のRT企画 |
| AI系YouTuber/ブロガーに紹介依頼 | YouTube/Blog | 無料ツールなので紹介しやすい |
| LangChain/LlamaIndex等のコミュニティDiscordで紹介 | Discord | 「Aigisでscan()追加した」使い方 |
| Qiita/Zennで週1記事（ユースケース別） | Qiita/Zenn | 「金融向け」「医療向け」「行政向け」 |
| GitHub Awesome List への掲載申請 | GitHub | awesome-llm-security等 |

### Phase 3: 持続成長（1-3ヶ月）

**目標: 1,000+ スター、月間ダウンロード1,000+**

| アクション | チャネル | 備考 |
|-----------|---------|------|
| Contributor向けのgood-first-issue整備 | GitHub | 外部コントリビューターを呼び込む |
| 「Policy Template Hub」公開 | GitHub/サイト | Guardrails AIの「Hub」に相当。業種別ポリシー |
| AI Security Conference登壇 | カンファレンス | 「個人開発でAIガバナンスOSSを作った話」 |
| 企業の導入事例1本 | サイト/記事 | 自社（議事録AI）でもOK |
| Product Hunt Launch | Product Hunt | 英語圏への拡大 |

---

## 記事の最適投稿タイミング

| プラットフォーム | ベストタイミング | 理由 |
|----------------|----------------|------|
| Qiita | 火〜木曜の8:00-9:00 | 通勤中のエンジニアが見る。週前半がトレンド入りしやすい |
| Zenn | 月〜水曜の朝 | 同上 |
| HackerNews | 日本時間 21:00-23:00（EST 8-10AM） | 米国東部の朝。最もアクティブな時間帯 |
| Twitter/X | 12:00（昼休み）or 21:00（夜） | エンジニアのTwitterタイム |
| Reddit | 日本時間 22:00-24:00 | 米国の朝〜午前 |
| はてなブックマーク | 記事投稿直後に3ブクマ | 「新着」に載る閾値 |

---

## 収益化ロードマップ

### 短期（0-3ヶ月）: 無料で認知拡大
- OSSのまま無料提供
- GitHub Sponsorsを開設（月$5〜のティア）
- 記事のZenn有料部分（技術解説の深堀り）

### 中期（3-6ヶ月）: フリーミアムモデル
| 機能 | Free | Pro（検討中） |
|------|------|-------------|
| scan() / sanitize() | 無制限 | 無制限 |
| Policy Engine (14ルール) | 無制限 | 無制限 |
| Activity Stream (ローカル) | 無制限 | 無制限 |
| グローバル集約 | ローカルのみ | クラウド集約 |
| ダッシュボード | CLI | **Web UI** |
| チーム管理 | なし | **複数メンバー** |
| Slack/Teams通知 | なし | **リアルタイム** |
| SLA付きサポート | なし | **あり** |

### 長期（6ヶ月〜）: エンタープライズ
- クラウドホスティング版（SaaS）
- LDAP/SSO連携
- 複数エージェント統合管理
- カスタムポリシーコンサルティング

---

## 試すべきアプローチ（個人開発なので全部試す）

### バイラル系
- [ ] Gandalf Challenge完走スクショをTwitterでシェア企画
- [ ] 「AIエージェントにrm -rf /させてみた → Aigisが止めた」動画
- [ ] 「情シスが泣いて喜ぶOSSを作った」系のキャッチー記事

### SEO系
- [ ] 「AIエージェント セキュリティ 対策」でZenn記事上位狙い
- [ ] 「Claude Code 安全 使い方」でQiita記事上位狙い
- [ ] 「AI事業者ガイドライン 対応 ツール」でサイトSEO

### コミュニティ系
- [ ] LangChain/LlamaIndex Discordで「Aigis使ってみた」
- [ ] AI系Meetupで5分LT「個人開発でAIガバナンスOSS作った話」
- [ ] GitHub Discussions有効化 → Q&Aコミュニティ形成

### パートナー系
- [ ] 他のOSS（LangChain等）へのIntegration PR
- [ ] 「Aigis x LangChain」のチュートリアル記事
- [ ] MCP Gateway（Lasso）との連携プラグイン

---

## KPI

| 期間 | GitHub Stars | PyPIダウンロード/月 | 記事いいね合計 |
|------|-------------|-------------------|-------------|
| 1週間後 | 50 | 100 | 50 |
| 1ヶ月後 | 300 | 500 | 200 |
| 3ヶ月後 | 1,000 | 2,000 | 500 |
| 6ヶ月後 | 3,000 | 5,000 | — |

Sources:
- [How to Get Your First 1,000 GitHub Stars](https://dev.to/iris1031/how-to-get-your-first-1000-github-stars-the-complete-open-source-growth-guide-4367)
- [10K Stars in 18 Months (Real Data)](https://dev.to/iris1031/github-star-growth-10k-stars-in-18-months-real-data-4d04)
- [個人開発OSSでGitHub Star 2.3kを獲得するまで](https://zenn.dev/yohamta/articles/25581c19b45c5f)
- [The Playbook for Getting More GitHub Stars](https://www.star-history.com/blog/playbook-for-more-github-stars)
