# Aigis Trust Pack — AI Agent Adoption Approval / AIエージェント導入承認パック

> **📋 This is a real sample, committed so you can see the output before installing.**
> Everything below was produced by `aigis trust-pack` from a fresh `aigis init --agent claude-code --policy enterprise` demo project — only this callout is hand-written.
> Generate your own in ~30 seconds: `pip install pyaigis && aigis init --agent claude-code --policy enterprise && aigis trust-pack --lang both`.
> Prefer one printable file? Open [`aigis-trust-pack.html`](./aigis-trust-pack.html) (download → open in a browser → print to PDF → email to your security team).
>
> **📋 これは実際の生成サンプルです**（インストール前に出力を確認できるよう同梱しています）。
> 以下はすべて `aigis init --agent claude-code --policy enterprise` した直後のデモプロジェクトで `aigis trust-pack` を実行して生成したもので、手書きはこの囲みだけです。
> ご自身の環境では約30秒で生成できます: `pip install pyaigis && aigis init --agent claude-code --policy enterprise && aigis trust-pack --lang both`。

This pack contains the documents an IT / information-security department reviews before approving Claude Code (or another autonomous AI agent) for company use. Every document is generated from the **live local Aigis configuration** — policy, hooks, and audit logs — not from marketing claims.

本パックは、情報システム部門がClaude Code（または他の自律型AIエージェント）の社内利用を承認する際に確認する文書一式です。各文書は、マーケティング上の主張ではなく、**稼働中のローカルAigis設定**（ポリシー・フック・監査ログ）から生成されています。

## Pack metadata / パック情報

- **Generated at / 生成日時:** 2026-08-14T05:57:54.555056+00:00
- **Aigis version / バージョン:** 1.2.0
- **Organisation / 組織:** Example Corp（サンプル株式会社）
- **Security contact / セキュリティ窓口:** security@example.com
- **Languages / 言語:** en, ja

## Live posture summary / 現状サマリ

- Active policy / 適用ポリシー: **Aigis Enterprise Policy** (v1.0) — 16 rules (10 deny / 5 review / 1 allow)
- Claude Code hook / フック: **configured / 設定済み**
- Activity logs / 監査ログ: **no logs yet / ログなし**
- Signed audit log / 署名付き監査ログ: **enabled / 有効**

## Contents / 収録文書

- [`01_executive_summary.md`](./01_executive_summary.md) — Executive summary / エグゼクティブサマリ (en)
- [`01_executive_summary.ja.md`](./01_executive_summary.ja.md) — Executive summary / エグゼクティブサマリ (ja)
- [`02_control_matrix.md`](./02_control_matrix.md) — Control matrix / コントロールマトリクス (en)
- [`02_control_matrix.ja.md`](./02_control_matrix.ja.md) — Control matrix / コントロールマトリクス (ja)
- [`03_policy_snapshot.md`](./03_policy_snapshot.md) — Policy snapshot / ポリシースナップショット (en)
- [`03_policy_snapshot.ja.md`](./03_policy_snapshot.ja.md) — Policy snapshot / ポリシースナップショット (ja)
- [`04_audit_log_evidence.md`](./04_audit_log_evidence.md) — Audit log evidence / 監査ログの証跡 (en)
- [`04_audit_log_evidence.ja.md`](./04_audit_log_evidence.ja.md) — Audit log evidence / 監査ログの証跡 (ja)
- [`05_incident_runbook.md`](./05_incident_runbook.md) — Incident runbook / インシデント対応手順 (en)
- [`05_incident_runbook.ja.md`](./05_incident_runbook.ja.md) — Incident runbook / インシデント対応手順 (ja)
- [`06_rollout_plan.md`](./06_rollout_plan.md) — Rollout plan / 展開計画 (en)
- [`06_rollout_plan.ja.md`](./06_rollout_plan.ja.md) — Rollout plan / 展開計画 (ja)

---

_Honesty principle: this pack is generated from the live local configuration. Organisation-specific items (data classification, approver names, escalation contacts) appear as explicit `[TO FILL: ...]` / `【要記入: ...】` fields for you to complete. Compliance mappings are presented as supporting evidence, not as a certification or guarantee of compliance._
