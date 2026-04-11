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
