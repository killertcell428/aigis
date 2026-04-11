---
title: "aigisのClaude Code Hookが動かない！原因調査から`aig doctor`誕生まで"
emoji: "🔍"
type: "tech"
topics: ["Claude Code", "AI", "セキュリティ", "Python", "OSS"]
published: false
---

## はじめに

[aigis](https://github.com/killertcell428/aigis)は、AIエージェントの操作を監視・制御するLLMセキュリティミドルウェアです。Claude Code、Cursor、カスタムエージェントなど、あらゆるAIエージェントのツール呼び出しをインターセプトし、脅威スキャン・ポリシー評価・ログ記録を行います。

aigisの中核的なユースケースの一つが、**Claude Code Hookとしての動作**です。Claude Codeには`PreToolUse`というフックポイントがあり、Bash実行やファイル書き込みなど全てのツール呼び出しの「直前」に外部スクリプトを実行できます。aigisはこのフックに割り込み、操作内容をスキャンして、ポリシーに違反していればブロックします。

```
Claude Code がツールを呼ぶ
    │
    ▼ PreToolUse hook
[aig-guard.py]
    ├─ stdinからツール情報を受け取る
    ├─ 脅威スキャン（48パターン）
    ├─ ポリシー評価（allow / deny / review）
    ├─ Activity Streamにログ記録
    │
    ▼
exit 0 → 許可 / exit 2 → ブロック
```

セットアップは2コマンドで完了します。

```bash
pip install aigis
aig init --agent claude-code
```

これで `.claude/settings.json` にhook設定が書き込まれ、`.claude/hooks/aig-guard.py` が生成されます。あとはClaude Codeを使うだけで、全操作が自動的に記録・評価される――はずでした。

## Claude Code Hookの仕組み

本題に入る前に、Claude Code Hookの仕組みを少し詳しく説明します。

Claude Codeは `.claude/settings.json` にhook定義を書くことで、ツール呼び出しの前後にコマンドを実行できます。aigisが生成する設定はこんな感じです。

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/aig-guard.py\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

`matcher: ".*"` で全ツールにマッチし、`aig-guard.py` が呼ばれます。このスクリプトはstdinからJSON形式のツール呼び出し情報を受け取ります。

```python
input_data = json.loads(sys.stdin.read())

tool_name = input_data.get("tool_name", "")    # "Bash", "Write", etc.
tool_input = input_data.get("tool_input", {})   # ツールの引数
session_id = input_data.get("session_id", "")
cwd = input_data.get("cwd", os.getcwd())
```

受け取ったツール名はaigisの内部アクション名にマッピングされます。

```python
action_map = {
    "Bash": "shell:exec",
    "Read": "file:read",
    "Write": "file:write",
    "Edit": "file:write",
    "Glob": "file:search",
    "Grep": "file:search",
    "WebFetch": "network:fetch",
    "WebSearch": "network:search",
    "Agent": "agent:spawn",
    "NotebookEdit": "file:write",
}
if tool_name.startswith("mcp__"):
    return "mcp:tool_call"
```

MCPツールも `mcp:tool_call` として捕捉します。そしてこのアクション情報を元にポリシー評価・スキャン・ログ記録を行い、最終的に `sys.exit(0)`（許可）か `sys.exit(2)`（ブロック）で結果を返します。

## 「ログが出ない」事件

ある日、aigisの動作確認をしていて異変に気づきました。

**ローカルのログファイルが空っぽ。**

`aig logs` を叩いても `No events found.` しか返ってこない。Claude Codeでさんざんツールを使っているのに、`.aigis/logs/` には何も記録されていません。

一方、グローバルログ（`~/.aigis/global/`）を見ると...こちらにはデータがある。ただし、それは以前の別プロジェクトのログでした。今のプロジェクトからのイベントは一件もありません。

最初に疑ったのはログパスの問題です。`ActivityStream` のコンストラクタはデフォルトで `.aigis/logs` にログを書きます。カレントディレクトリの問題か？ cwdが違う場所を指しているのか？

```python
class ActivityStream:
    def __init__(
        self,
        log_dir: str = ".aigis/logs",
        enable_global: bool = True,
        enable_alerts: bool = True,
    ):
        self.local_dir = Path(log_dir)
        self.local_dir.mkdir(parents=True, exist_ok=True)
```

デバッグログを仕込んで確認してみましたが、パスは正しい。ファイルの作成権限も問題ない。

次に `aig-guard.py` 自体にprint文を入れてみました。stderrに出力すればClaude Codeの画面に表示されるはずです。

...何も出ない。

**hookが呼ばれていない。**

`settings.json` の設定は正しい。スクリプトも存在する。なのにhookが一切発火しない。これはaigis側の問題ではなく、Claude Code側でhookの実行自体がスキップされている、ということです。

## 原因: `disableAllHooks: true`

Claude Codeの設定ファイルを改めて調べ直しました。`.claude/settings.json` は正しい。では `.claude/settings.local.json` は？

```json
{
  "disableAllHooks": true
}
```

**犯人はこいつでした。**

`disableAllHooks: true` はClaude Codeの設定で、文字通り全てのhookを無効化するフラグです。`settings.json` でどれだけhookを定義しても、`settings.local.json` に `disableAllHooks: true` があると全てが無視されます。

:::message alert
`settings.local.json` は `settings.json` を上書きするローカル設定ファイルです。gitignoreに含まれることが多く、チームメンバーには見えません。自分で設定したことすら忘れがちです。
:::

なぜこんな設定が入っていたかというと、以前hookのデバッグ中に「一旦hookを全部止めて素の状態で確認したい」と思って設定し、**戻し忘れた**のです。

たった1行の設定ミスで、セキュリティミドルウェアが完全に沈黙していた。しかもエラーは一切出ない。ログも出ない。まるで最初から存在しないかのように、静かに無効化されていた。

## `aig doctor`の誕生

この問題を二度と起こさないために、**セットアップ診断コマンド** `aig doctor` を実装しました。

8項目のヘルスチェックを実行し、問題があれば具体的な対処法を表示します。

```python
def cmd_doctor(args) -> int:
    """Diagnose Aigis setup issues."""
    print("Aigis Doctor")
    print("=" * 50)

    # 1. Policy file
    # 2. .aigis/logs/ directory
    # 3. aigis module importable
    # 4. Claude Code hook script
    # 5. Claude Code settings.json has hook configured
    # 6. Check disableAllHooks in settings.local.json  ← これが本命
    # 7. Check for recent log activity
    # 8. Check global log directory
```

特に今回の原因だった `disableAllHooks` の検出は、こうなっています。

```python
# 6. Check disableAllHooks in settings.local.json
local_settings_path = Path(".claude/settings.local.json")
if local_settings_path.exists():
    try:
        raw = local_settings_path.read_bytes()
        text = raw.decode("utf-8-sig") if raw[:3] == b"\xef\xbb\xbf" else raw.decode("utf-8")
        local_settings = json.loads(text)
        if local_settings.get("disableAllHooks", False):
            fail(
                "disableAllHooks=true in settings.local.json -- "
                "ALL hooks are disabled! "
                "Set to false or remove the key to enable Aigis."
            )
        else:
            ok("Hooks are enabled (disableAllHooks is not set)")
    except (json.JSONDecodeError, UnicodeDecodeError, Exception) as e:
        warn(f"Cannot parse settings.local.json: {e}")
else:
    ok("No settings.local.json overrides")
```

BOM付きUTF-8にも対応しています（Windowsで生成されたJSONファイルでたまに遭遇するため）。

実際の出力例はこんな感じです。

```
$ aig doctor
Aigis Doctor
==================================================
  [OK]   Policy file found: aigis-policy.yaml
  [OK]   Log directory exists: .aigis/logs
  [OK]   aigis module imports OK
  [OK]   Hook script found: .claude/hooks/aig-guard.py
  [OK]   PreToolUse hook configured in settings.json
  [FAIL] disableAllHooks=true in settings.local.json -- ALL hooks are disabled! Set to false or remove the key to enable Aigis.
  [WARN] No log files found. If you've used Claude Code recently, the hook may not be firing.
  [OK]   Global logs: 3 file(s)

Results: 5/8 passed, 1 warnings, 1 FAILED

Fix the FAIL items above, then run 'aig doctor' again.
```

チェック項目7の「最近のログ活動」も重要です。hookが設定されているのにログがなければ、何かがおかしい。FAILにはしませんがWARNを出します。hookが呼ばれていない可能性を示唆するメッセージです。

## `aig init`への警告追加

`aig doctor` は「事後の診断」ですが、そもそもセットアップ時に気づけるようにもしました。`aig init --agent claude-code` 実行時にも `disableAllHooks` を検出して警告します。

```python
def _warn_if_hooks_disabled(project_dir: str = ".") -> None:
    """Check if Claude Code hooks are disabled and warn the user."""
    local_settings = Path(project_dir) / ".claude" / "settings.local.json"
    if not local_settings.exists():
        return
    try:
        raw = local_settings.read_bytes()
        text = raw.decode("utf-8-sig") if raw[:3] == b"\xef\xbb\xbf" else raw.decode("utf-8")
        data = json.loads(text)
        if data.get("disableAllHooks", False):
            print()
            print("  WARNING: disableAllHooks=true in .claude/settings.local.json")
            print("  All Claude Code hooks are disabled -- Aigis will NOT run.")
            print("  Fix: set disableAllHooks to false, or remove the key.")
    except (json.JSONDecodeError, UnicodeDecodeError, Exception):
        pass
```

さらに、`install_hooks()` 関数内でも `warnings.warn()` を発行するようにしました。

```python
# adapters/claude_code.py の install_hooks() 内
local_settings_path = project / ".claude" / "settings.local.json"
if local_settings_path.exists():
    try:
        local_data = json.loads(local_settings_path.read_text(encoding="utf-8"))
        if local_data.get("disableAllHooks", False):
            import warnings
            warnings.warn(
                "disableAllHooks=true in .claude/settings.local.json — "
                "Aigis hooks will NOT run. "
                "Set disableAllHooks to false to enable.",
                stacklevel=2,
            )
    except (json.JSONDecodeError, Exception):
        pass
```

:::message
`aig init` 実行時に「hookをインストールしました」と表示された直後に「でもhookは無効化されています」という警告が出るのは少し間抜けに見えるかもしれません。でも、それでいいんです。ユーザーが気づけることが最優先です。
:::

## まとめ

今回の問題は、aigisのコードのバグではありませんでした。`settings.local.json` という、**ユーザー側の設定ファイル**に原因がありました。

でも、だからといって「ユーザーの設定ミスです」で終わりにするのは、OSSとして不誠実だと思います。

セキュリティツールが「静かに無効化される」のは最悪のシナリオです。エラーが出るならまだいい。ログが出るならまだいい。何も出ないまま「守られている」と思い込んでいる状態が一番危険です。

OSSの品質は「正しく動くこと」だけでは不十分で、**「設定ミスを検出して教えること」**まで含めて品質です。特にセキュリティツールにおいては、サイレントな無効化は機能的なバグと同等の深刻さを持ちます。

`aig doctor` はたかだか100行ちょっとのコードですが、こういう「あるある」な設定トラブルを即座に発見してくれます。新しいプロジェクトでaigisをセットアップしたら、まず `aig doctor` を叩く。これを習慣にしておけば、「hookが動いてなかった」という事故は防げます。

```bash
# セットアップ後の習慣にしよう
aig init --agent claude-code
aig doctor
```

aigisはまだ開発初期段階のOSSですが、こういったDXの改善を積み重ねて、「AIエージェント時代のセキュリティ基盤」として育てていきたいと考えています。

:::message
aigisに興味を持った方は、[GitHub](https://github.com/killertcell428/aigis)をチェックしてみてください。Star、Issue、PRなんでも歓迎です。
:::
