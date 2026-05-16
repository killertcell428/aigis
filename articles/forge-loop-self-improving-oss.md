---
title: "Claude Code に OSS の継続改善を全任せする — Forge Loop 設計と Aigis 17 サイクル運用記"
emoji: "🔥"
type: "tech"
topics: ["claudecode", "ai", "oss", "AIエージェント", "自動化"]
published: false
---

![Forge Loop overview](https://raw.githubusercontent.com/killertcell428/aigis/master/images/forge-loop/og.png)

## TL;DR

- Claude Code エージェントを **定期起動**して、自分の OSS を **調査 → 実装 → テスト → GitHub リリース** まで自走させる仕組みを作った
- セキュリティスキャナ [Aigis](https://github.com/killertcell428/aigis) で **5 日 / 17 サイクル / 11 リリース (v1.0.1 → v1.0.12)** を半自動運用
- 肝は「AI に何を任せ、人がどこに線を引くか」の設計
- この設計パターンを **Forge Loop** と名付け、汎用化したものを [GitHub](https://github.com/killertcell428/forge-loop) で公開

---

## まず Aigis の 1 サイクルを見てもらう

2026 年 5 月 11 日 06:12 UTC、私は寝ている。Aigis の CI で Claude Code エージェントが起動する。
([実物の研究メモはこちら](https://github.com/killertcell428/forge-loop/tree/main/examples/aigis/snapshot/research/2026-05-11T06-12_6-multi-agent.md))

```
T+0:00   ROTATION.md を読む
           NEXT_INDEX: 6 → 今回のドメインは "multi-agent"

T+0:30   research/2026-05-11T06-12_6-multi-agent.md を新規作成
           arxiv / Unit42 / Keysight / LevelBlue から A2A protocol 攻撃を調査
           → Agent Session Smuggling (Unit42, April 2025)
           → Agent Card Poisoning (Keysight + LevelBlue, March 2026)
           → Promptware Kill Chain (arxiv:2601.09625)
           → MASpi benchmark, など 7 件の調査ソース

T+15:00  changes/2026-05-11T06-12_changes.md に実装案を記録

T+20:00  aigis/multi_agent/message_scanner.py に regex を 2 グループ追加
           _AGENT_CARD_POISONING_PATTERNS (3 rules, 19 LOC)
           _SESSION_FABRICATION_PATTERNS  (3 rules, 21 LOC)

T+25:00  tests/test_multi_agent.py に 8 ケース追加
           pytest → 1222 pass · 16 pre-existing failures · 4 skipped

T+27:00  3 つ目のアイデア (Agent spoofing 検出) は metadata-layer の検証必須
         → content scanner では実装不可能
         → pending/2026-05-08_agent-spoofing-metadata-validation.md に隔離

T+30:00  累積ルール 5 件 (前回 supply-chain 3 + 今回 multi-agent 2)
         → ≥3 件 threshold クリア → v1.0.12 patch bump

T+32:00  CHANGELOG 追記 + git tag v1.0.12
T+33:00  GitHub Actions が tag を検知 → PyPI 自動公開
T+34:00  INDEX.md に 1 行追記 → エージェント終了
```

朝起きてリリースノートを眺めると、**自分が一切タッチしていないバージョンが PyPI に上がっている**。

![Forge Loop 1 cycle anatomy](https://raw.githubusercontent.com/killertcell428/aigis/master/images/forge-loop/loop.png)

5 日間でこれを 17 回繰り返した結果が、現在の Aigis の状態:

| 指標 | 値 |
|---|---|
| 累積サイクル数 | **17** |
| 累積 Pending | **22 件** |
| リリース回数 | **11** (v1.0.1 → v1.0.12, v1.0.5 はスキップ) |
| Pending に積まれた提案 | **22 件** (人レビュー待ち) |
| Release を打たなかった cycle | 6 (累積しきい値未達) |

実データは [examples/aigis/snapshot/](https://github.com/killertcell428/forge-loop/tree/main/examples/aigis/snapshot/) に丸ごと置いてある。
INDEX.md / ROTATION.md / 全 pending を読めば実運用がそのまま見える。

---

## 「AI に任せる」が普通は失敗する理由

実は最初の数回はうまくいかなかった。AI に「OSS を良くしておいて」と丸投げすると、こうなる:

| 失敗モード | 何が起きるか |
|---|---|
| **題材偏り** | 毎回プロンプトインジェクションばかり触る (流行 / 楽な題材に流れる) |
| **思考の蒸発** | 「考えました」だけで何も残らない、後から監査できない |
| **暴走 PR** | 「API 全部書き換えます」と巨大 PR を出してリポジトリが壊れる |
| **無限ループ** | どこで止めればいいか分からず、同じ修正を延々繰り返す |

逆に、AI に **「次は X ファイルの Y 行を Z に変えろ」**みたいな厳格な脚本を渡すと、決まりきった改修しか出さなくなる。AI を使う意味がない。

**この中間を設計するのが Forge Loop。** AI に裁量を与えつつ、暴走させない外枠を作る。

---

## 主役の主張

![Boundary design](https://raw.githubusercontent.com/killertcell428/aigis/master/images/forge-loop/boundary.png)

**外枠を人が決め、中身を AI に任せる。**

| 層 | 誰が決めるか | 内容 |
|---|---|---|
| **外枠** | 人 | ドメイン一覧 / 段階の規約 / 保留ルール / リリース判定 |
| **中身** | AI | 各ドメインで何を調べる / どう実装する / どのテストを足す |

これが「人と AI の境界線」。AI に「中身の裁量」だけを与えて、「枠の設計権」は人が握る。

---

## 境界線の引き方 — 3 つの具体テクニック

### ① Rotate (巡回) — 「何を改善するか」を AI に選ばせない

ドメイン一覧を `domains.yaml` のような形で **人が手で書く**。実行時は `ROTATION.md` の `NEXT_INDEX` を mod N で進めるだけ。

```markdown
# auto-improvement/ROTATION.md

NEXT_INDEX: 7
LAST_RUN_UTC: 2026-05-11T06-12

## 領域定義
| # | キー | 主たる調査対象 |
|---|------|--------------|
| 0 | prompt-injection | 直接 / 間接 / multi-modal 注入 |
| 1 | agent-tool-abuse | tool / MCP 濫用、confused deputy |
| 2 | data-exfiltration | データ漏洩、出力チャネル悪用 |
| 3 | jailbreak-extraction | jailbreak、system prompt 抽出 |
| 4 | memory-context | メモリ汚染、RAG poisoning |
| 5 | supply-chain-llm | model / dataset / dep 攻撃 |
| 6 | multi-agent | A2A protocol、agent card poisoning |
| 7 | evasion-obfuscation | encoding、homoglyph、policy bypass |
| 8 | compliance-regulation | NIST、EU AI Act 等の更新 |
| 9 | incident-postmortems | CVE、ベンダーアドバイザリ |
```

エージェントの初動は必ず **「ROTATION.md を読む」**から始まる。今日何をやるかの選択権は AI にない。

これが効くのは、**メタ判断 (何をやるか) こそ AI が最も暴走しやすい場所**だから。中身の判断は安定するが、メタ判断は流行や直前の文脈に簡単に引きずられる。

### ② Materialize (物質化) — AI の思考を必ずファイルに落とす

各段階の出力が必ずディレクトリに残る規約:

```
auto-improvement/
├── research/                                 # 段階1: 調査
│   └── 2026-05-11T06-12_6-multi-agent.md
├── changes/                                  # 段階2: 実装案 + 結果
│   └── 2026-05-11T06-12_changes.md
├── pending/                                  # 段階3: 保留
│   └── 2026-05-08_agent-spoofing-metadata-validation.md
└── INDEX.md                                  # 全実行の追記式ログ
```

これは見た目はファイル整理だが、本質は **「考えただけ」「実装したけど記録なし」を構造的に不可能にする**こと。

実装フェーズで「research/ を読み込んで、changes/ に書き、コードを変更し、tests/ にテストを追加する」を **規約**にしておくと、AI はこの流れから外れられない。外れたら後から見て一目で分かるので、是正できる。

長期間 AI に任せるとき、これがないと「先週何があったか」が霧消する。**監査可能性こそが「任せる」を成立させる**。

### ③ Defer (保留) — 完了 / 失敗の二択にしない

破壊的 / 大規模 / 不確実な提案は実装せず、`pending/` に隔離する。判定基準は明文化しておく:

```markdown
# Pending 行きの判定基準
- 100 LOC を超える変更
- API breaking change (公開関数のシグネチャ変更等)
- 既存テストを書き換える必要がある
- セキュリティ的に確信度が低い
- 新規ランタイム依存の追加
```

Aigis の `pending/` には現在 **22 件**積まれている (実例は [examples/aigis/snapshot/pending/](https://github.com/killertcell428/forge-loop/tree/main/examples/aigis/snapshot/pending/))。代表例:

- [`crescendo-multiturn-detection`](https://github.com/killertcell428/forge-loop/tree/main/examples/aigis/snapshot/pending/2026-05-08_crescendo-multiturn-detection.md)
  — 多ターン jailbreak 検出。200 LOC 超 & 公開 API シグネチャ変更が必要
- [`agent-spoofing-metadata-validation`](https://github.com/killertcell428/forge-loop/tree/main/examples/aigis/snapshot/pending/2026-05-08_agent-spoofing-metadata-validation.md)
  — 暗号署名が必要、content scanner では実装不可能
- [`nist-ai-critical-infra-template`](https://github.com/killertcell428/forge-loop/tree/main/examples/aigis/snapshot/pending/2026-05-09_nist-ai-critical-infra-template.md)
  — 大規模 compliance template、方針判断が必要

これらは **失敗ではなく "意図的な先送り"**。設計通り。

「やらない判断」を AI に許すと、AI は「危なそうなものは pending」と書いて次に進む。許さないと、AI は **「とにかく実装する」**に倒れる。これが暴走の主犯。

---

## なぜこのタイミングで書くのか

執筆時点 (2026-05) で、AI に OSS の改修を **本当に任せている**事例は意外と少ない:

| よくある事例 | Forge Loop |
|---|---|
| AI が PR をレビューする | AI が PR を作って merge して release する |
| AI がドキュメント生成 | AI が機能を増やしてリリースする |
| 単発タスク (1 回限り) | 数時間おきに 17 回続いた |
| 多エージェント実験 | シングルエージェント本番運用 |
| 「やってみた」記事 | 半自動でリリースし続けている事実 |

「やればできる」が広く知られていないだけで、技術的には Claude Code + GitHub Actions + 規約だけで足りる。難しいのはコードではなく **境界線設計**。

---

## 自分の OSS でやるなら

Forge Loop は Aigis に特化していない。「ドメイン × 段階 × 保留」の3つは何の OSS でも書ける:

| OSS タイプ | ドメイン例 |
|---|---|
| **Linter** | 言語別 (Python / TS / Go ...) |
| **ドキュメント生成** | 章別 (API / Tutorial / FAQ / Error messages) |
| **CLI ツール** | subcommand 別 |
| **テストカバレッジ拡張** | ファイル群別 |
| **i18n リソース** | 言語別 |

成果物は [forge-loop リポジトリ](https://github.com/killertcell428/forge-loop) に置いた。`template/` をコピーして `domains.yaml` を書き換えれば、3 分で開始できる。

---

## 失敗事例 (この記事の "もう一つの主役")

きれい事を書いたが、実際は何回か事故っている。

### 事故 1: pending 判定をプロンプトに任せて 110 LOC が暴走

最初は `defer_thresholds.max_loc_per_change = 100` を **プロンプトに書いていただけ**だった。
ある cycle で AI が「110 LOC ですが本質的には 1 つの変更です」と判断して実装し、テストが通ったので tag が打たれた。

→ **学び**: 判定はプロンプトではなく LOC カウントなど機械的指標で実施。

### 事故 2: research/ が空のまま implement に直行

外部 API が落ちていて research が空ファイルになった cycle。AI は「知識ベースから」と称して既存知識で 3 件実装した。事故ではないが、**研究知見のないルールが生産された**のは問題。

→ **学び**: 各段階の成果物存在を次段階の開始条件にする (research/<date>.md に最低 1 つの URL が無いと changes/ に書けない)。

### 事故 3: regex の初版が現実と合っていない

Cycle 6 で agent card poisoning の regex が `route\s+to` を要求していたが、実際の攻撃文は "route requests to" (動詞と目的語の間に語が入る)。

→ **学び**: cycle 内でのテスト失敗→修正が回せている。これは Materialize の効能 (changes/*.md に修正過程が記録される)。

---

## このパターンは他に何に使えるか

OSS の継続改修以外にも適用できそうな領域:

- **社内ドキュメントの継続改善** (ドメイン = 章 / 部署)
- **データセット品質の継続改善** (ドメイン = カテゴリ)
- **ブログサイトの自動運営** (ドメイン = テーマ)
- **マーケティングコンテンツ生成** (ドメイン = プロダクト機能)
- **Q&A bot のナレッジ拡張** (ドメイン = カテゴリ / 製品)

共通するのは **「ドメインが N 個あり、それぞれを継続的に育てたい」**シチュエーション。

---

## まとめ

- Claude Code は「使い切り」ではなく「常駐」させると、複利でリポジトリが育つ
- AI に裁量を与えるなら **境界線を人が引く**
- 境界線の引き方は **巡回 / 物質化 / 保留** の 3 つで足りる
- 監査可能な形で残せば、後から人が修正できる
- 失敗は隠さず `pending/` で見える化する

Aigis での運用ログと Plugin は [forge-loop リポジトリ](https://github.com/killertcell428/forge-loop) で公開しています。実 ROTATION.md / 全 22 pending / サンプル research・changes が `examples/aigis/snapshot/` に丸ごと入っているので、生データを見たい方はそちらをどうぞ。

---

## 参考

- [Forge Loop リポジトリ](https://github.com/killertcell428/forge-loop) — 設計と参考実装
- [Aigis (実例の OSS)](https://github.com/killertcell428/aigis) — Forge Loop が動いている実 OSS
- [Aigis 実データスナップショット](https://github.com/killertcell428/forge-loop/tree/main/examples/aigis/snapshot/) — 全 17 サイクル + 17 pending
