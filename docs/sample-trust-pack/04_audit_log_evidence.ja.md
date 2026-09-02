# 4. 監査ログの証跡

## ログの保存場所

Aigisは監査ログを3階層で保持します（いずれも追記専用のJSONL形式、1行1イベント）。

- **ローカルログ:** `.aigis\logs`（プロジェクト単位、開発者が確認可能）
- **グローバルログ:** `~/.aigis/global/`（全プロジェクト横断、監査・CISO向け）
- **アラート保管:** `~/.aigis/alerts/`（拒否・レビューイベントを恒久保存）

現状: ローカルログは未生成、直近7日間で0件、30日間で0件を記録しています。

## イベントスキーマ（JSONLフィールド）

各イベントは `aigis.activity.ActivityEvent` として記録され、以下のフィールドを持ちます。

- `action`
- `target`
- `agent_type`
- `user_id`
- `session_id`
- `event_type`
- `cwd`
- `project_name`
- `details`
- `risk_score`
- `risk_level`
- `matched_rules`
- `remediation_hints`
- `owasp_refs`
- `policy_decision`
- `policy_rule_id`
- `timestamp`
- `event_id`
- `autonomy_level`
- `delegation_chain`
- `estimated_cost`
- `memory_scope`
- `suggested_fix`
- `fix_applied`

## 保持・ローテーション

- 完全ログは既定で60日間保持し、それ以降は自動でローテーション（圧縮または削除）されます。
- アラートログ（`~/.aigis/alerts/`）は恒久保存され、削除されません。
- ローテーション・圧縮は次のコマンドで実行します: `aigis maintenance`

## 改ざん検知の設計

署名付き監査ログ（`aigis.audit.SignedAuditLog`）は、各エントリに対して次を行います。

1. **HMAC-SHA256署名** — 各エントリの全フィールドを正準JSON化し、秘密鍵で署名します。
   署名はそのエントリの内容に依存するため、1バイトでも改変すれば署名検証に失敗します。
2. **ハッシュチェーン** — 各エントリは直前エントリのSHA-256ハッシュ（`prev_hash`）を保持
   します。これにより、エントリの削除・並べ替え・挿入が検知可能になります。

整合性は次の4チェックで検証されます: 署名・チェーン・連番・タイムスタンプ順序。

**検証コマンド:**

```
aigis audit verify
```

`--log PATH` でログファイルを指定でき、`--json` で機械可読な結果を出力します。
状態確認には `aigis audit status` を使用します。
現状: 署名付き監査ログは有効です。

## 鍵の管理 — 改ざん検知を信頼する前に確認すること

HMAC鍵は次の順序で解決されます（`aigis/audit/signed_log.py`）。

1. 呼び出し側が明示的に渡した `secret_key`
2. 既存の鍵ファイル `.aigis/audit_key`
3. いずれも無ければ新規生成（`secrets.token_hex(32)`）して同ファイルに保存

**審査する側が知っておくべきこと。** 既定構成では、署名鍵はエージェントとログと
同じマシン上に、同じユーザー権限で置かれます。したがって署名が検知できるのは
「ログを書いた本人以外」による改変です — 後続プロセス、別ユーザー、ファイル破損。
**本人がエントリを書き換えて再署名した場合は検知できません。** 鍵を本人が持って
いるからです。

記録対象である開発者本人を脅威モデルに含める場合 — 監査ログを置く理由は通常
そこにあります — 署名ログを次のいずれかと組み合わせてください。

- **SIEM転送**（次節）。Splunk / Sentinel / Elastic / Datadog に複製されたイベントは
  開発者の手が届かない場所に残ります。現時点で最も強い選択肢で、Aigis側の変更は
  不要です。
- **外部で保持する鍵。** 開発者が読めないシークレットマネージャから `secret_key` を
  渡せば、ローカルでの偽造ができなくなります。
- **`~/.aigis/alerts/` の外部エクスポート。** 開発者が書き込めない保管先へ定期的に出す。

プラットフォーム注記: 鍵ファイルはPOSIXでは `0600` を設定しますが、Windowsは
POSIX権限を強制しません。Windows環境ではNTFS ACLを明示的に設定してください。

## SIEM転送

イベントは任意で外部SIEMへ転送できます（Elastic Common Schema形式、HTTP）。転送は
非ブロッキングで、エージェントのツール呼び出しを遅延させません。送信前に個人情報の
墨消し（Redactor）を実行できます。詳細は `docs/forwarders.md` を参照してください。
現状: 未検出（転送設定はコードで行うため。docs/forwarders.md を参照）。
