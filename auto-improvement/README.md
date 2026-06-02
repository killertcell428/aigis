# auto-improvement/

aigis を 6 時間ごとに自動強化する保守ループの作業領域。
人間が直接編集する場所ではなく、リモート保守エージェントが書き込む台帳。

## ディレクトリ

| パス | 内容 |
|------|------|
| `ROTATION.md` | 10 領域ローテ定義 + 現在のカウンタ。毎回 +1 (mod 10) される |
| `INDEX.md` | 全実行回の時系列インデックス（1 行サマリ） |
| `research/` | 各回のリサーチレポート (UTC 名: `YYYY-MM-DDTHH-MM_NN-<domain>.md` または `..._paper-batch.md`) |
| `changes/` | 各回の改修記録（追加機能・テスト結果・対応リサーチへのリンク） |
| `pending/` | 大幅方向転換の提案。実装は保留。人間が後で採否を判断 |
| `paper_review_state.json` | 後述「論文レビューループ」で読み終えた URL/タイトルの台帳 |
| `scripts/paper_review.py` | 論文レビューループ本体（毎日 GH Actions から起動） |

## 論文レビューループ（2026-05 追加）

[Awesome-LLM4Cybersecurity](https://github.com/tmylla/Awesome-LLM4Cybersecurity) を毎日 10 件ずつ読み進める半自動ループ。`.github/workflows/paper-review.yml` が 00:15 UTC に走り、`scripts/paper_review.py` が以下を行う：

1. 上流 `LITERATURES.md` を fetch
2. `paper_review_state.json` の既読 URL/タイトルを除外し、未読の新しい順から 10 件ピック
3. 各論文を Claude Haiku 4.5 に渡し、「Aigis に regex/部分一致で落とせる検出器候補があるか」を JSON で判定
4. relevant=true のものを `pending/YYYY-MM-DD_paper_<slug>.md` として draft 化
5. バッチ全体のサマリを `research/YYYY-MM-DDTHH-MM_paper-batch.md` に書き出し
6. `gh issue create` でレビュー依頼 Issue を 1 本オープン
7. 変更を bot ブランチで PR 化（人間がレビュー → master へマージ）

実装は一切しない。pending/ に積まれた候補は、既存のルール（[ROTATION.md](ROTATION.md)）と同じく、人間が個別 PR で `aigis/` 配下に昇格させる。

**必要な secrets:** `ANTHROPIC_API_KEY`（Anthropic console から発行、Settings → Secrets → Actions に登録）。未設定なら workflow は失敗するが、`workflow_dispatch` から `dry_run=true` でドライ実行は可能。

**コスト目安:** 10 件 × Haiku 4.5（≈500 出力トークン）≈ 数¢/日。月 $1 弱を想定。

## 運用ルール（保守エージェントが守る）

- **各サイクルの最初に必ず `make setup-git` を実行**する。フックと `format.signoff` を有効化し、DCO チェックの取りこぼしを防ぐ。fresh worktree/container で実行する場合の必須ブートストラップ
- AI による機能追加は禁止（aigis のゼロ依存・ルールベース路線維持）
- `README.md` は触らない（人手メンテ領域）
- 既存テストが 1 件でも失敗する変更は実装しない（pending 送り）
- 破壊的 API 変更／新規ランタイム必須依存／100 行超の構造変更／ゼロ依存方針逸脱 → pending
- リリース判定は **蓄積型**: 新規ルール/検出器/可視化が累積 3 件以上、または compliance template 追加、またはユーザー視点で意味のある hardening が溜まった時のみ patch bump
- 1 回の実行は 1 ローテ領域だけを扱う

## 人間の役割

- `pending/` を定期的に眺めて、採否を判断する
- 大きな機能拡張・路線変更は人間が `pending/` を昇格 or 別ブランチで実装
- リリースノートは `CHANGELOG.md` を読めば時系列で全変更が把握できる

## リリース手順（必ずこの順序を守る）

タグから feature ブランチを切らない。**master にマージされたコミットからのみタグを打つ**。
`release.yml` は `merge-base --is-ancestor origin/master` の guard で orphan commit からのリリースを拒否する。

### 必須: 毎回 `release_preflight.sh` を通すこと

タグを push する直前に [`auto-improvement/scripts/release_preflight.sh`](scripts/release_preflight.sh) を実行する。失敗した場合は **何もせずに人間に escalate** する。bump して retry してはいけない（[Issue #56](https://github.com/killertcell428/aigis/issues/56) で documented した v1.1.2 / v1.1.3 cascade の原因）。

```bash
./auto-improvement/scripts/release_preflight.sh vX.Y.Z $(git rev-parse origin/master)
# exit 0 → push 可
# exit 2 → タグ衝突。bump 禁止、人間判断待ち
# exit 3 → master 未到達 (orphan)。先に PR を merge
# exit 4 → master tip ではない。新しい変更を取り込む
```

### 標準フロー

1. feature ブランチで release コミット（`release: vX.Y.Z`）と `uv.lock` 更新を作成
2. PR を開き、CI / レビューを通して **master にマージ**
3. master の HEAD（マージ後のコミット）に対して preflight → タグ
   ```bash
   git checkout master && git pull
   ./auto-improvement/scripts/release_preflight.sh vX.Y.Z
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```
4. タグ push が `release.yml` を起動 → PyPI 公開 → GitHub Release 作成

### NG パターン（過去に v1.1.0〜v1.1.3 で発生 — Issue #56）

- feature ブランチの HEAD からタグを打って push する → orphan commit から公開されてしまう
- PR が master にマージされずに残るため、CHANGELOG とソースツリーが一致しない
- 次サイクルで「tag collision」を理由に version bump を再試行し、orphan tag を量産する
- 失敗時に `_unpushed_<timestamp>.patch` artifact をコミット → 履歴を汚染する（このパターンも禁止）
