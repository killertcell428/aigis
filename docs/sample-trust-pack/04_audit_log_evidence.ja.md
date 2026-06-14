# 4. 監査ログの証跡

## ログの保存場所

Aigisは監査ログを3階層で保持します（いずれも追記専用のJSONL形式、1行1イベント）。

- **ローカルログ:** `.aigis/logs`（プロジェクト単位、開発者が確認可能）
- **グローバルログ:** `~/.aigis/global/`（全プロジェクト横断、監査・CISO向け）
- **アラート保管:** `~/.aigis/alerts/`（拒否・レビューイベントを恒久保存）

現状: ローカルログは未生成、
直近7日間で0件、30日間で0件を記録しています。

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
現状: 署名付き監査ログは利用可能（未有効化）です。

## SIEM転送

イベントは任意で外部SIEMへ転送できます（Elastic Common Schema形式、HTTP）。転送は
非ブロッキングで、エージェントのツール呼び出しを遅延させません。送信前に個人情報の
墨消し（Redactor）を実行できます。詳細は `docs/forwarders.md` を参照してください。
現状: not detected (forwarders are configured in code; see docs/forwarders.md)。
