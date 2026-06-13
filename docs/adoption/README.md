# Bringing Claude Code to your company — adoption guide

This guide maps the journey from "an engineer wants to use Claude Code" to
"IT and security have approved it and rollout is underway."

It is written for mixed audiences: engineers who want to move fast, and
IT/security reviewers who need evidence before they sign off.

---

## The adoption journey

```
Engineer requests Claude Code
         │
         ▼
IT/Security review ──► "What data leaves? Who controls what it can do?
         │               Where are the logs? Which frameworks does this meet?"
         │
         ▼
Two-layer control model answers every question
  Layer 1 — Claude Code enterprise controls (managed-settings.json via MDM)
  Layer 2 — Aigis PreToolUse hook + policy + tamper-evident audit
         │
         ▼
aigis trust-pack generates approval package (ISO 27001 / NIST AI RMF /
         │          OWASP LLM Top 10 / 経産省AI事業者ガイドラインv1.2)
         │
         ▼
Pilot → departmental rollout → org-wide
```

Both layers are required. Neither alone is sufficient. See
[two-layer-architecture.md](two-layer-architecture.md) for the full picture.

---

## Files in this guide

| File | Audience | Purpose |
|------|----------|---------|
| **This file** | All | Overview and navigation |
| [it-security-checklist.md](it-security-checklist.md) | IT / security reviewers | ~15 questions IT actually asks, each answered with (a) Claude Code built-ins, (b) what Aigis adds, (c) org responsibility |
| [it-security-checklist.ja.md](it-security-checklist.ja.md) | 情報システム・セキュリティ担当者 | 上記の日本語版 |
| [two-layer-architecture.md](two-layer-architecture.md) | Architects / security engineers | How the two layers fit together; honest scope table |
| [two-layer-architecture.ja.md](two-layer-architecture.ja.md) | アーキテクト・セキュリティ担当者 | 上記の日本語版 |

---

## Related documents

| Document | Notes |
|----------|-------|
| [../../README.md](../../README.md) | Aigis project overview, quick start, full feature list |
| [../trust-pack.md](../trust-pack.md) | `aigis trust-pack` reference — generates the full approval package |
| [../configuration.md](../configuration.md) | Aigis policy YAML and Guard constructor reference |
| [../forwarders.md](../forwarders.md) | SIEM forwarder setup (Splunk, Sentinel, Datadog, Elastic) |
| [../compliance/](../compliance/) | Framework mapping details (ISO 27001, NIST, OWASP) |

---

## Quick start for the IT reviewer

You have been asked to approve Claude Code + Aigis for internal use. The
fastest path to a structured answer:

```bash
# 1. Install Aigis
pip install 'pyaigis[all]'

# 2. Initialise the Claude Code integration with enterprise policy
aigis init --agent claude-code --policy enterprise

# 3. Generate the approval package (English + Japanese, HTML)
aigis trust-pack --lang both --format html

# 4. Open it
open aigis-trust-pack/index.html   # or start aigis-trust-pack\index.html on Windows
```

The trust pack contains: executive summary, control matrix, policy snapshot,
audit evidence specification, incident runbook, and rollout plan. Fields that
require org-specific decisions are marked `[TO FILL]`.

---

## Quick start for the engineer

```bash
pip install 'pyaigis[all]'
aigis init --agent claude-code --policy enterprise
# → installs .claude/hooks/aig-guard.py
# → creates aigis-policy.yaml
# Restart Claude Code — every tool call is now scanned before execution.

aigis doctor          # verify hook wiring and log paths
aigis monitor --owasp # live OWASP LLM Top 10 scorecard
```

---

## 日本語版について

ITセキュリティ部門向けのドキュメントは日本語版を用意しています。

- [it-security-checklist.ja.md](it-security-checklist.ja.md) — 情報システム・セキュリティ部門向けチェックリスト
- [two-layer-architecture.ja.md](two-layer-architecture.ja.md) — 二層アーキテクチャの解説

承認パッケージ（Trust Pack）も日本語出力に対応しています。

```bash
aigis trust-pack --lang ja --format html
```

---

## What Aigis does not do

Be precise with stakeholders:

- Aigis does **not** make your organisation "ISO 27001 compliant" — it
  produces evidence for relevant controls; certification requires a full ISMS.
- Aigis is deterministic pattern/policy-based. It will not catch novel
  deep-semantic attacks that do not match any pattern.
- Aigis does not control what happens inside Anthropic's cloud (model
  inference). See [two-layer-architecture.md](two-layer-architecture.md) §
  "What neither layer covers."
- Aigis is a defence-in-depth layer, not a guarantee.
