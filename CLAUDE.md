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

### Tag ordering — never tag before merging to master

The release workflow (`.github/workflows/release.yml`) refuses to publish if the tagged commit is not reachable from `origin/master` (orphan-tag guard). Always:

1. Land the `release: vX.Y.Z` commit on master via PR merge first.
2. Only then create and push tag `vX.Y.Z` against the master commit.

Pushing a tag from a feature branch HEAD will fail the release workflow and waste a version number. If you hit a "tag collision" error, **do not bump the version and retry from the same orphan commit** — that is the pattern that produced the v1.1.1 → v1.1.2 → v1.1.3 cascade of unreachable releases. Investigate why master doesn't have the release commit instead.

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

**Tests:** <PASS> pass · <FAIL> fail · <SKIP> skipped
```

### Test count — measured, never templated

The `**Tests:**` line is the single most-quoted fact in every release note. It MUST be the **actual output** of `uv run pytest` immediately before the release commit. Past releases got this wrong by copy-pasting "16 pre-existing failures" from earlier cycles even when the real number was 0 — do not repeat that mistake.

Required procedure for every release (Step 7 and Step 11):

1. Run `uv run pytest --tb=no -q 2>&1 | tail -3` and capture the last line, which looks like `1332 passed in 51.25s` or `13 failed, 1268 passed in 48.41s`.
2. Read the three numbers directly off that line — do not infer, do not reuse the previous release's numbers, do not write "N pre-existing failures" as if it were a constant.
3. If `failed` > 0, the `**Tests:**` line must name the failing test file(s) and one of:
   - the commit/PR that will fix them (if a fix is in flight), or
   - "investigation in progress, see issue #NNN" (if not yet fixed).
   Never label a real failure as "pre-existing" without a citation — that phrasing is what hid the v1.0.13/v1.0.14 `test_gpai_provider` regression in the published notes.
4. CHANGELOG entry (Step 7) and GitHub release body (Step 11) MUST agree on the three numbers. If they disagree, the release is wrong.

### What NOT to do

- Do not write a single-line bullet that names an attack but gives no example.
- Do not omit the rule ID — it is what developers look up in logs.
- Do not omit the measured ASR or source — this is what justifies the rule.
- Do not copy the `**Tests:**` line from a prior release — measure it fresh every cycle.


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
