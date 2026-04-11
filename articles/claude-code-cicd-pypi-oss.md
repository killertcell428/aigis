---
title: "OSSのCI/CD＋PyPI公開をClaude Codeだけで構築した話"
emoji: "🚀"
type: "tech"
topics: ["Claude Code", "GitHub Actions", "PyPI", "CI/CD", "OSS"]
published: false
---

## はじめに

LLMアプリをプロンプトインジェクションやPII漏洩から守るPythonライブラリ **aigis** をOSSとして開発しています。

https://github.com/killertcell428/aigis

このプロジェクトのCI/CD、PyPI公開、リリースフローの全てを **Claude Codeとの対話だけ** で構築しました。手動でGitHub ActionsのYAMLを書いたり、PyPIのドキュメントを読みに行ったりは一切していません。

「PyPI公開したいんだけど」「CIも欲しい」「タグ打ったら自動リリースして」と会話しただけで、本記事で紹介する一式が出来上がりました。

この記事では、実際に生成されたファイルを元に、何が構築されたかを解説します。

## 構築したもの全体像

最終的に出来上がったのは以下の3ファイルです。

```
.github/workflows/
  ci.yml        # push/PR時の品質チェック
  release.yml   # タグpush時の自動リリース
Makefile          # ローカル開発コマンド集
pyproject.toml    # パッケージ定義
```

フローを図にするとこうなります。

```
push / PR → ci.yml
  ├── lint (ruff) + type-check (mypy)
  ├── test (pytest × 3 Python × 3 OS)
  └── build (twine check)

git tag v*.*.* → release.yml
  ├── build (wheel + sdist)
  ├── PyPI publish (OIDC trusted publishing)
  └── GitHub Release (auto-changelog)

make install-dev / test / lint / build
  └── ローカル開発の全操作を1コマンドで
```

## ci.yml の設計

### Lint & Type Check

CIの最初のジョブはlintと型チェックです。ruff（lint + format check）と mypy を順番に実行します。

```yaml
lint:
  name: Lint & Type Check
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Set up Python 3.11
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"
        cache: pip

    - name: Install dev dependencies
      run: pip install -e '.[dev]'

    - name: ruff lint
      run: ruff check aigis/ tests/

    - name: ruff format check
      run: ruff format --check aigis/ tests/

    - name: mypy type check
      run: mypy aigis/
```

### マトリクスビルド + スモークテスト戦略

テストジョブが今回一番工夫されたポイントです。

```yaml
test:
  name: Test / Python ${{ matrix.python-version }}
  runs-on: ${{ matrix.os }}
  strategy:
    fail-fast: false
    matrix:
      python-version: ["3.10", "3.11", "3.12"]
      os: [ubuntu-latest]
      include:
        # Windows smoke test on latest Python only
        - python-version: "3.12"
          os: windows-latest
        # macOS smoke test on latest Python only
        - python-version: "3.12"
          os: macos-latest
```

**ポイント:**

- Ubuntu上でPython 3.10 / 3.11 / 3.12 の3バージョンをフルテスト
- Windows / macOS はPython 3.12のみのスモークテスト
- `fail-fast: false` で、1つ落ちても他のマトリクスは続行

全組み合わせ（3 x 3 = 9）を回すとCIが遅くなるので、クロスプラットフォームは最新Pythonだけに絞っています。Claude Codeがこの判断を自動でやってくれたのは正直驚きました。

### Codecovアップロード

カバレッジはUbuntu + Python 3.11の組み合わせだけアップロードします。

```yaml
- name: Upload coverage
  uses: codecov/codecov-action@v4
  if: matrix.python-version == '3.11' && matrix.os == 'ubuntu-latest'
  with:
    files: coverage.xml
    fail_ci_if_error: false
    token: ${{ secrets.CODECOV_TOKEN }}
```

### Concurrency制御

地味に嬉しいのがこれ。同じブランチへの連続pushで、古いCI実行が自動キャンセルされます。

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

### ビルドチェック

最後にパッケージが正しくビルドできるか確認します。

```yaml
build:
  name: Build package
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Build wheel and sdist
      run: python -m build
    - name: Check distribution
      run: twine check dist/*
    - name: Store distributions
      uses: actions/upload-artifact@v4
      with:
        name: dist
        path: dist/
```

`twine check` でメタデータの不備（READMEのレンダリングエラーなど）をCIの段階で検出できます。

## release.yml の設計

### タグトリガー

リリースは `v0.1.0` のようなセマンティックバージョニングのタグをpushすると自動で走ります。

```yaml
on:
  push:
    tags:
      - "v[0-9]+.[0-9]+.[0-9]+"
      - "v[0-9]+.[0-9]+.[0-9]+[ab][0-9]+"  # alpha/beta tags
```

`v0.5.0a1`（アルファ）や `v0.5.0b2`（ベータ）にも対応しているのが気が利いています。

### Trusted Publishing（OIDCでトークン不要）

PyPIへの公開には **Trusted Publishing** を使っています。これがrelease.ymlの最大のポイントです。

```yaml
permissions:
  contents: write   # GitHub Release creation
  id-token: write   # PyPI Trusted Publishing (OIDC)

# ...

publish-pypi:
  name: Publish → PyPI
  needs: build
  runs-on: ubuntu-latest
  environment:
    name: pypi
    url: https://pypi.org/p/aigis

  steps:
    - name: Download distributions
      uses: actions/download-artifact@v4
      with:
        name: python-package-distributions
        path: dist/

    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      # No username/password needed — uses OIDC trusted publishing.
```

:::message
**Trusted Publishingとは？**
PyPIのAPIトークンをGitHub Secretsに保存する代わりに、GitHub ActionsのOIDCトークンでPyPIに認証する仕組みです。PyPI側でリポジトリとワークフローを登録するだけで、シークレット管理が不要になります。
:::

### 前のタグの自動検出とChangelog生成

GitHub Releaseには、前回タグからのコミットを自動でchangelogとして載せます。

```yaml
- name: Find previous tag
  id: prev-tag
  run: |
    PREV=$(git tag --sort=-version:refname | grep -v "^${GITHUB_REF_NAME}$" | head -1)
    echo "tag=${PREV}" >> "$GITHUB_OUTPUT"

- name: Generate changelog
  id: changelog
  env:
    PREV_TAG: ${{ needs.build.outputs.prev-tag }}
    VERSION: ${{ github.ref_name }}
  run: |
    if [ -n "$PREV_TAG" ]; then
      RANGE="${PREV_TAG}..HEAD"
    else
      RANGE="HEAD"
    fi

    # Group commits by conventional-commit prefix
    FEATURES=$(git log $RANGE --pretty=format:"- %s (%h)" --no-merges \
      --grep="^feat" | head -20)
    FIXES=$(git log $RANGE --pretty=format:"- %s (%h)" --no-merges \
      --grep="^fix" | head -20)
    # ...
```

Conventional Commits（`feat:` / `fix:` / `chore:` etc.）に従ってコミットメッセージを書いていれば、リリースノートが "New Features" / "Bug Fixes" / "Other Changes" に自動分類されます。

## pyproject.toml の設計

### ゼロ依存コア + Optional Dependencies

aigisのコアライブラリは **外部依存ゼロ** です。

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "aigis"
version = "0.4.0"
description = "Protect your LLM application from prompt injection, PII leaks, and jailbreaks"
requires-python = ">=3.11"
# Zero required dependencies for the core library
dependencies = []
```

必要な機能だけをoptional dependenciesとしてインストールできます。

```toml
[project.optional-dependencies]
yaml = ["pyyaml>=6.0"]
fastapi = ["fastapi>=0.115.0", "starlette>=0.41.0"]
langchain = ["langchain-core>=0.1.0"]
openai = ["openai>=1.0.0"]
server = [
    "aigis[yaml,fastapi,openai]",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy>=2.0.0",
    # ... more server deps
]
all = ["aigis[yaml,fastapi,langchain,openai]"]
dev = [
    "aigis[all]",
    "pytest>=8.2.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
    # ... more dev deps
]
```

使う側は用途に応じて選べます。

```bash
pip install aigis             # コアのみ
pip install aigis[fastapi]    # FastAPIミドルウェア付き
pip install aigis[all]        # 全インテグレーション
pip install aigis[dev]        # 開発用（テスト・lint含む）
```

### CLIエントリポイント

`aig` コマンドでCLIが使えます。

```toml
[project.scripts]
aig = "aigis.cli:main"
```

## Makefile による開発体験

ローカル開発はMakefileで1コマンド完結です。

```makefile
install-dev:
	$(PIP) install -e '.[dev]'

test:
	pytest $(TESTS)/ -v

lint:
	ruff check $(SRC)/ $(TESTS)/

format:
	ruff format $(SRC)/ $(TESTS)/

type-check:
	mypy $(SRC)/

check: lint format-check type-check
	@echo "\nAll checks passed."

build: clean
	$(PYTHON) -m build
	twine check dist/*
```

日常的に使うのはこの4つです。

```bash
make install-dev   # 初回セットアップ
make test          # テスト実行
make check         # CI相当のチェック（lint + format + type-check）
make build         # パッケージビルド
```

:::message
`make check` がCI上の `lint` ジョブと同じチェックを実行するので、pushする前にローカルで確認できます。
:::

## PyPI公開で踏んだ罠

ここからはClaude Codeでは解決できなかった話です。

最初、パッケージ名を `aigis` にしていました。`pyproject.toml` にもそう書いていたし、当然そのまま公開できると思っていました。

**しかし、`aigis` は既に別の人に取られていました。**

PyPIには既に `aigis` v1.1.1 が存在しており、全く別のプロジェクトでした。`pip install aigis` すると見知らぬパッケージが入ります。

結局、パッケージ名を **`aigis`** に変更して解決しました。

:::message alert
**教訓: パッケージ名は事前にPyPI JSON APIで確認する**

```bash
# 名前が使えるかチェック（404なら未使用）
curl -s -o /dev/null -w "%{http_code}" https://pypi.org/pypi/your-package-name/json
```

200が返ってきたら既に取られています。Claude Codeはこのチェックをやってくれないので、人間が確認する必要があります。
:::

## gitタグの運用

リリースは `git tag` で行います。v0.1.0からv0.4.0まで、以下のようにタグを打ってきました。

```bash
# タグを作ってpush
git tag v0.4.0
git push origin v0.4.0
```

これだけで release.yml が発火し、PyPI公開 + GitHub Release作成が自動で走ります。

開発中、release.ymlの修正後にタグを打ち直したい場面がありました。その場合はリモートのタグを削除してから再作成します。

```bash
# リモートのタグを削除
git push origin :refs/tags/v0.4.0

# ローカルのタグを削除
git tag -d v0.4.0

# 再作成してpush
git tag v0.4.0
git push origin v0.4.0
```

:::details タグ打ち直しの注意点
タグの打ち直しは開発初期のみに留めるべきです。既にユーザーがいるバージョンのタグを消すと、再現性が失われます。v1.0.0以降は絶対にやらないようにしましょう。
:::

## まとめ

Claude Codeに「PyPI公開したい」と伝えるだけで、以下が全て構築されました。

- **ci.yml**: マトリクスビルド（3 Python x 3 OS）、lint、型チェック、カバレッジ
- **release.yml**: タグトリガー、OIDC trusted publishing、自動changelog
- **Makefile**: ローカル開発コマンド一式
- **pyproject.toml**: hatchling、ゼロ依存コア、optional dependencies

YAMLの書き方を調べたり、PyPIのドキュメントを読んだりする時間がゼロになりました。Trusted Publishingのような比較的新しい仕組みも、Claude Codeが知識として持っているので、最初からベストプラクティスで構築されます。

**ただし、パッケージ名の事前確認だけは人間がやるべきです。** これは外部サービスの状態に依存するため、AIには判断できません。

CI/CDやリリースフローは「一度作ればあとは触らない」タイプの作業なので、AIとの対話で一気に構築するのは非常に相性が良いと感じました。
