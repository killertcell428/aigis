# Aigis — Project Guidelines

## Zenn記事管理（Zenn CLI + GitHub連携）

Zenn記事・書籍はZenn CLIとGitHub連携で管理する。Playwrightやブラウザ操作での投稿は行わない。

### ディレクトリ構成
- `articles/` — Zenn記事（slug形式のファイル名: `my-article-slug.md`）
- `books/` — Zenn書籍
- `content/articles/` — 他プラットフォーム向け下書き（Qiita, dev.to等）

### 記事の作成
```bash
npx zenn new:article --slug <slug-name>
```
slugは英数字・ハイフンで12-50文字。`articles/` に自動生成される。

### プレビュー
```bash
npx zenn preview
```
http://localhost:8000 でプレビュー確認。

### 記事の公開
1. frontmatterの `published: true` に変更
2. git commit & push → Zenn側に自動反映

### 記事の非公開・下書き
- `published: false` にしてpush

### npm scripts
- `npm run zenn:preview` — プレビューサーバー起動
- `npm run zenn:new:article` — 新規記事テンプレート生成
- `npm run zenn:new:book` — 新規書籍テンプレート生成
- `npm run zenn:list:articles` — 記事一覧表示

---

## Auto-Improvement Loop — Release Note & CHANGELOG Format

**IMPORTANT: This section OVERRIDES the "one short user-visible sentence" instruction in the loop's Step 7 and Step 11. Write release notes at the level of detail specified here.**

### CHANGELOG entries (Step 7)

Each entry under `## [Unreleased]` must cover **every new `DetectionPattern` or detector** added in the cycle. For each one, write:

```markdown
- **`rule_id`** (score N, input/output filter) — One sentence: what attack it detects and what
  a blocked example looks like. Include: attack name, source (paper/org/year), and measured
  attack success rate if available.

  **Blocked example:**
  ```
  [concrete example of the input or output that would be flagged]
  ```
```

Keep individual entries concise but complete — a reader must be able to answer:
1. Which rule was added (ID)?
2. What does it catch?
3. What does a real attack look like?
4. Why does it matter (ASR / source)?

### GitHub release body (Step 11)

The GitHub release body must be **at least as detailed as the CHANGELOG entries** for the same version. Use this structure:

```markdown
## What changed

**N new [detector type] detectors** (`file/path.py`)

Research basis: [Paper title (arxiv:XXXXXXX), Org name, Year]

---

### `rule_id` — Short attack name (score N)

[1–2 sentences: what the attack is, who documented it, and the measured ASR.]

**Example blocked input/output:**
```
[concrete verbatim example]
```

[Optional: one sentence on false-positive tuning or caveats.]

---

[Repeat for each rule]

---

**Tests:** N pass · N pre-existing failures · N skipped
```

### What NOT to do

- Do not write a single-line bullet that names an attack but gives no example.
- Do not omit the rule ID — it is what developers look up in logs.
- Do not omit the measured ASR or source — this is what justifies the rule.


Zenn記事・書籍はZenn CLIとGitHub連携で管理する。Playwrightやブラウザ操作での投稿は行わない。

### ディレクトリ構成
- `articles/` — Zenn記事（slug形式のファイル名: `my-article-slug.md`）
- `books/` — Zenn書籍
- `content/articles/` — 他プラットフォーム向け下書き（Qiita, dev.to等）

### 記事の作成
```bash
npx zenn new:article --slug <slug-name>
```
slugは英数字・ハイフンで12-50文字。`articles/` に自動生成される。

### プレビュー
```bash
npx zenn preview
```
http://localhost:8000 でプレビュー確認。

### 記事の公開
1. frontmatterの `published: true` に変更
2. git commit & push → Zenn側に自動反映

### 記事の非公開・下書き
- `published: false` にしてpush

### npm scripts
- `npm run zenn:preview` — プレビューサーバー起動
- `npm run zenn:new:article` — 新規記事テンプレート生成
- `npm run zenn:new:book` — 新規書籍テンプレート生成
- `npm run zenn:list:articles` — 記事一覧表示
