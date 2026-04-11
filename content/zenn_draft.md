---
title: "AIエージェント導入で「セキュリティどうするの？」と聞かれたときの技術的な答え方"
emoji: "🛡️"
type: "tech"
topics: ["AI", "セキュリティ", "LLM", "ガバナンス", "Python"]
published: false
---

## この記事を読んでほしい人

- Claude Code / Cursor などのAIエージェントを**チームに導入したい**エンジニア
- 情シスから「セキュリティ面の対応は？」と聞かれて**技術的に答えたい**人
- AIツール導入の**セキュリティ面の検討材料**を探している情シス担当

:::message
本記事はAIエージェントのセキュリティ面の技術対策に焦点を当てています。実際の導入判断には、コスト・運用体制・社内規程・契約面など他の要素も必要です。ここで紹介するのは「技術的にはこういう対策が取れます」という材料です。
:::

## AIエージェント導入で必ず聞かれる3つの質問

AIエージェントの導入を提案すると、情シスやセキュリティ部門からだいたいこう聞かれます。

> **Q1: 「AIが何をしてるか見えないけど大丈夫？」**
> **Q2: 「危険な操作を勝手にされない？」**
> **Q3: 「何かあったとき説明できる？」**

どれも正当な懸念です。そしてこれらは実は**技術的に対応可能**です。

## 技術的な対策の全体像

```
AIエージェント（Claude Code等）
    │ すべてのツール呼び出し
    ▼
[Aigis] ← pip install aigis で導入
    │
    ├─ Activity Stream: 全操作をログ記録
    ├─ Policy Engine: ルールベースで操作を制御
    ├─ Threat Scanner: 48パターンで脅威を検知
    │
    ▼
Allow（実行許可）/ Deny（ブロック）/ Review（要確認）
```

これは[Aigis](https://github.com/killertcell428/aigis)というOSSで実現できます。セットアップは2コマンドです。

```bash
pip install aigis
aig init --agent claude-code
```

## Q1への技術的回答：「全操作を自動記録しています」

`aig init` するとClaude Codeの全ツール呼び出しがActivity Streamに自動記録されます。

```bash
$ aig logs

         Time          Action                         Target  Risk Decision
--------------------------------------------------------------------------------
  15:30:00        shell:exec                          ls -la     0     OK
  15:30:05        file:read                     src/main.py     0     OK
  15:30:10       file:write                     src/main.py     0     OK
  15:31:02        shell:exec                   git push ...     0    REV
  15:32:15        shell:exec                    rm -rf /tmp    90  BLOCK
```

**記録される情報：**
- 誰が（OS ユーザー名）
- いつ（タイムスタンプ）
- 何を（shell:exec, file:read, file:write 等）
- どこで（ファイルパス、コマンド内容）
- リスク判定（0-100のスコア）
- ポリシー判定（許可/ブロック/要確認）

**ログの保管場所：**

| 層 | 場所 | 用途 | 保持期間 |
|---|------|------|---------|
| ローカル | `.aigis/logs/` | エンジニアが自分の操作を確認 | 60日 |
| グローバル | `~/.aigis/global/` | 組織横断の監査用 | 60日 |
| アラート | `~/.aigis/alerts/` | ブロック・要確認の履歴 | 無期限 |

Excel出力もできるので、定期報告に使えます。

```bash
aig logs --export-excel monthly_report
# → monthly_report_summary.csv（集計）
# → monthly_report_events.csv（全イベント）
```

## Q2への技術的回答：「ポリシーで操作を制御しています」

`aigis-policy.yaml` に定義したルールで、エージェントの操作を自動制御します。

```yaml
# aigis-policy.yaml（デフォルトで14ルール入り）
rules:
  - id: dangerous_commands
    action: "shell:exec"
    target: "rm -rf *"
    decision: deny
    reason: "再帰削除はブロック"

  - id: env_file_protection
    action: "file:write"
    target: ".env*"
    decision: deny
    reason: "環境変数ファイルの書き込みを禁止"

  - id: git_push_review
    action: "shell:exec"
    target: "git push*"
    decision: review
    reason: "pushは確認が必要"
```

**デフォルトで入っている主なルール：**

| ルール | 対象 | 判定 |
|--------|------|------|
| 再帰削除（rm -rf） | shell:exec | ブロック |
| 環境変数ファイル書込 | file:write .env* | ブロック |
| SSH鍵アクセス | file:* .ssh/* | ブロック |
| 認証情報ファイル | file:write *credentials* | ブロック |
| リモートスクリプト実行 | shell:exec *\| bash* | ブロック |
| Force push | shell:exec *--force* | ブロック |
| Git push | shell:exec git push* | 要確認 |
| 特権昇格（sudo） | shell:exec sudo * | 要確認 |
| サブエージェント生成 | agent:spawn * | 要確認 |

ルールはYAMLファイルなので、gitで管理でき、チームでレビューできます。

## Q3への技術的回答：「監査証跡とコンプライアンスレポートがあります」

```bash
$ aig status

Aigis - Governance Status
==================================================
  Policy: Aigis Developer Policy (v1.0)
  Rules: 14 (9 deny, 4 review)

  Activity (last 7 days):
    Total events: 342
    Blocked: 8

  Compliance: 100.0% (24/24 covered)
```

Aigisは、日本の主要AI規制の技術要件への対応状況を自動で集計します。

```bash
$ aig report --days 30 --format json
```

**対応している規制の技術要件：**

| 規制 | 対応状況 |
|------|---------|
| AI推進法（2025年9月施行） | 技術要件 3/3 カバー |
| AI事業者ガイドライン v1.1 | 技術要件 10/10 カバー |
| AIセキュリティGL（総務省） | 技術要件 6/6 カバー |
| 個人情報保護法 / マイナンバー法 | 技術要件 3/3 カバー |
| 不正競争防止法 | 技術要件 1/1 カバー |
| 著作権法 | 技術要件 1/1 カバー |

:::message alert
これは「技術的な対策としてカバーしている」という意味です。法的な準拠を保証するものではなく、実際のコンプライアンス判断には法務・コンプライアンス部門の確認が必要です。
:::

## PII（個人情報）の自動検知と墨消し

エージェントが扱うテキストに個人情報が含まれている場合、自動検知と墨消しが可能です。

```python
from aigis import scan, sanitize

# マイナンバーを検知
result = scan("マイナンバーは１２３４５６７８９０１２です")
print(result.risk_score)    # 70
print(result.risk_level)    # "high"

# 自動墨消し（LLMに送る前に除去）
cleaned, _ = sanitize("電話番号は090-1234-5678です")
print(cleaned)  # "電話番号は[PHONE_REDACTED]です"
```

全角数字やゼロ幅文字を使った回避も正規化して検知します。

## 技術仕様まとめ

| 項目 | 内容 |
|------|------|
| 外部依存 | なし（Python標準ライブラリのみ） |
| 検知パターン | 48 regex + 40 類似度フレーズ |
| テスト | 162件（検知率100%、偽陽性率0%） |
| ポリシー | YAML、14デフォルトルール |
| ログ形式 | JSONL（grep可能、Excel出力対応） |
| ライセンス | Apache 2.0（OSS） |
| 対応エージェント | Claude Code（hooks統合）、他エージェントは拡張予定 |

## 導入手順

```bash
# 1. インストール
pip install aigis

# 2. 初期化（Claude Code hooks設定込み）
aig init --agent claude-code

# 3. 確認
aig status
aig policy show
```

以降、Claude Codeを使うたびに自動で監視・制御・記録されます。

## プロンプトインジェクション対策を体験する

Aigisの検知エンジンを体験できるゲームもあります。

> **[Gandalf Challenge](https://aigis-mauve.vercel.app/challenge)** — AIが守る秘密のパスワードを、プロンプトインジェクションで抽出してください。全7レベル。

## おわりに

AIエージェント導入の検討で「セキュリティどうするの？」と聞かれたとき、**技術的にはこういう対策が取れます**、という1つの選択肢として紹介しました。

もちろん、技術対策だけで導入が決まるわけではありません。コスト、運用体制、社内規程、契約面など、考慮すべきことは他にもあります。ただ、「技術面では準備できている」と言える状態は、検討を前に進めるための一歩にはなるはずです。

- [GitHub](https://github.com/killertcell428/aigis)
- [PyPI](https://pypi.org/project/aigis/)
- [アーキテクチャドキュメント](https://github.com/killertcell428/aigis/blob/main/ARCHITECTURE.md)
- [日本規制対応ドキュメント](https://aigis-mauve.vercel.app/docs/compliance/japan)
