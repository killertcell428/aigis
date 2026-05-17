# auto-improvement/

aigis を 6 時間ごとに自動強化する保守ループの作業領域。
人間が直接編集する場所ではなく、リモート保守エージェントが書き込む台帳。

## ディレクトリ

| パス | 内容 |
|------|------|
| `ROTATION.md` | 10 領域ローテ定義 + 現在のカウンタ。毎回 +1 (mod 10) される |
| `INDEX.md` | 全実行回の時系列インデックス（1 行サマリ） |
| `research/` | 各回のリサーチレポート (UTC 名: `YYYY-MM-DDTHH-MM_NN-<domain>.md`) |
| `changes/` | 各回の改修記録（追加機能・テスト結果・対応リサーチへのリンク） |
| `pending/` | 大幅方向転換の提案。実装は保留。人間が後で採否を判断 |

## 運用ルール（保守エージェントが守る）

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
