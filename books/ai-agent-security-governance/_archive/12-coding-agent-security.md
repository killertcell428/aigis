---
title: "AIコーディングエージェントの安全運用"
---

# AIコーディングエージェントの安全運用

## 対象ツール

本章では、開発チームで広く使われているAIコーディングエージェントのセキュリティ運用を解説します。

- **Claude Code**: Anthropicの CLI/IDE統合エージェント
- **GitHub Copilot**: GitHub/Microsoftのコード補完・エージェント
- **Cursor**: AIネイティブなコードエディタ
- **その他**: Windsurf、Cline、Aider等

これらのツールは**ファイルの読み書き、コマンド実行、外部通信**が可能であり、セキュリティ設定なしでの利用は重大なリスクを伴います。

## 即時対応：基本的なセキュリティ設定

### 1. 機密ファイルの保護

`.claudeignore`（Claude Code）や`.gitignore`を適切に設定し、AIエージェントが機密ファイルにアクセスしないようにします。

```gitignore
# .claudeignore
.env
.env.*
*.key
*.pem
*.p12
credentials.json
service-account.json
~/.ssh/
~/.aws/
~/.config/gcloud/
```

### 2. auto_approveの無効化

AIエージェントがツール呼び出しを自動承認する設定は、必ず無効にします。

```json
// Claude Code: .claude/settings.json
{
  "permissions": {
    "auto_approve": false,
    "require_confirmation": ["Bash", "Write", "Edit"]
  }
}
```

### 3. CLAUDE.mdによるポリシー定義

プロジェクトルートの`CLAUDE.md`に、セキュリティポリシーを明記します。

```markdown
# CLAUDE.md

## セキュリティルール（必須遵守）

### 禁止事項
- `.env`、`.env.*` ファイルの読み取り・変更
- `~/.ssh/`、`~/.aws/` 配下のファイルへのアクセス
- `rm -rf`、`sudo`、`chmod 777` の実行
- 外部URL（許可リスト外）へのHTTPリクエスト
- APIキーやパスワードをコードやコミットメッセージに含めること

### 許可された操作
- `./src/`、`./tests/` 配下のファイルの読み書き
- `npm test`、`npm run build` の実行
- `git status`、`git diff`、`git log` の実行
- localhost へのHTTPリクエスト（テスト目的）
```

### 4. pre-commitフックによる認証情報の検出

コミット前に認証情報の漏洩を自動検出します。

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

```python
# カスタム検出パターンの例
CREDENTIAL_PATTERNS = {
    "AWS Access Key":     r'AKIA[0-9A-Z]{16}',
    "OpenAI API Key":     r'sk-[a-zA-Z0-9]{48}',
    "Anthropic API Key":  r'sk-ant-[a-zA-Z0-9\-]{80,}',
    "GitHub Token":       r'ghp_[a-zA-Z0-9]{36}',
    "Private Key":        r'-----BEGIN (RSA |EC )?PRIVATE KEY-----',
    "Generic Secret":     r'(?i)(password|secret|token)\s*[=:]\s*["\'][^"\']{8,}',
}
```

## MCPサーバーの安全な利用

### 導入前チェックリスト

```
MCPサーバー導入前の確認事項:

□ ソースコードが公開されている（OSS）
□ npm audit / pip audit で既知の脆弱性がない
□ tool description に不審なパターンがない
  □ "ignore previous" を含まない
  □ "system:" を含まない
  □ ファイル読み取り指示（cat ~/. 等）がない
  □ 外部通信指示（curl, wget 等）がない
□ 要求する権限が必要最小限である
□ メンテナンスが継続されている（最終更新が6ヶ月以内）
□ ダウンロード数・スター数が妥当
□ バージョンを固定してインストール
```

### MCPサーバーのホワイトリスト運用

```json
// 組織として承認されたMCPサーバーのリスト
{
  "approved_mcp_servers": [
    {
      "name": "@anthropic/mcp-server-filesystem",
      "version": "1.2.3",
      "approved_date": "2026-03-15",
      "reviewer": "security-team",
      "restrictions": "read-only, project directory only"
    },
    {
      "name": "@anthropic/mcp-server-github",
      "version": "2.0.1",
      "approved_date": "2026-03-15",
      "reviewer": "security-team",
      "restrictions": "specific repos only"
    }
  ],
  "policy": "Only servers in this list may be installed. Others require security review."
}
```

## フック（Hooks）によるセキュリティ自動化

Claude Codeのフック機能を利用して、セキュリティチェックを自動化できます。

### PreToolUseフック：実行前チェック

```json
// .claude/settings.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "python security_hooks/check_command.py \"$TOOL_INPUT\""
      },
      {
        "matcher": "Write",
        "command": "python security_hooks/check_file_write.py \"$TOOL_INPUT\""
      }
    ]
  }
}
```

```python
# security_hooks/check_command.py
import sys
import json
import re

BLOCKED_COMMANDS = [
    r'rm\s+-rf\s+[/*]',
    r'curl\s+.*\|\s*(sh|bash)',
    r'wget\s+',
    r'ssh\s+',
    r'scp\s+',
    r'sudo\s+',
    r'chmod\s+777',
    r'cat\s+~/?\.(ssh|aws|env|config)',
]

def check_command(tool_input: dict) -> None:
    command = tool_input.get("command", "")
    for pattern in BLOCKED_COMMANDS:
        if re.search(pattern, command):
            print(f"BLOCKED: Command matches dangerous pattern: {pattern}")
            sys.exit(1)

if __name__ == "__main__":
    tool_input = json.loads(sys.argv[1])
    check_command(tool_input)
```

### PostToolUseフック：実行後監査

```python
# security_hooks/audit_log.py
import json
import datetime

def log_tool_use(event: dict) -> None:
    """ツール使用を監査ログに記録"""
    log_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "tool": event.get("tool"),
        "action": event.get("action"),
        "target": event.get("target"),
        "result_hash": hash(str(event.get("result", ""))[:1000]),
    }
    
    with open(".claude/audit.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
```

## チーム展開時のセキュリティ設定

### 設定の標準化

チーム全体で統一されたセキュリティ設定を使用するため、設定ファイルをリポジトリに含めます。

```
project/
├── .claude/
│   └── settings.json       # Claude Codeの権限設定
├── .claudeignore            # アクセス除外ファイル
├── CLAUDE.md                # AIエージェントのポリシー
├── .pre-commit-config.yaml  # コミット前チェック
└── security_hooks/          # セキュリティフック
    ├── check_command.py
    ├── check_file_write.py
    └── audit_log.py
```

### オンボーディングチェックリスト

```
新メンバーのAIコーディングエージェント設定:

□ 個人用のAPIキーを発行（チーム共有キーは使わない）
□ .claude/settings.json の権限設定を確認
□ .claudeignore が正しく機能することを確認
□ pre-commit フックがインストールされている
□ セキュリティポリシー（CLAUDE.md）を読了
□ 禁止操作のリストを理解している
□ インシデント発生時の報告フローを理解している
```

## 定期的なセキュリティレビュー

```
月次レビュー項目:

□ MCPサーバーの脆弱性チェック（npm audit）
□ APIキーのローテーション状況確認
□ 監査ログの異常パターン確認
□ 新しい攻撃手法への対応状況確認（本書の更新を参照）
□ チームメンバーのセキュリティ設定の遵守状況確認
```

AIコーディングエージェントは開発生産性を飛躍的に向上させますが、セキュリティ設定なしでの利用は「特権アカウントをパスワードなしで公開する」のと同等のリスクです。本章の設定を導入することで、安全性と生産性を両立できます。
