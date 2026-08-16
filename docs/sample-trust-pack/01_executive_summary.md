# 1. Executive Summary

**Organisation:** Example Corp（サンプル株式会社）
**Prepared for:** [TO FILL: IT / Information Security Department]
**Security contact:** security@example.com
**Generated:** 2026-08-16T15:03:20.485326+00:00 (Aigis v1.2.0)

## What Claude Code is

Claude Code is Anthropic's command-line coding agent. It reads and edits
files, runs shell commands, fetches web content, and can call external
tools (including Model Context Protocol servers) on a developer's machine
to complete software-engineering tasks autonomously. Because it executes
real actions on a real workstation, an uncontrolled deployment is a
meaningful operational and security risk.

## What Aigis adds

Aigis is a zero-dependency, open-source guardrail layer that sits between
the agent and the actions it wants to take. It provides three things an
IT/security department can rely on:

1. **Deterministic pre-execution guardrails.** A Claude Code *PreToolUse*
   hook intercepts every tool call. Aigis scans the request, evaluates it
   against your organisation's policy, and returns allow / review / deny
   **before** the action runs. Decisions are rule-based and reproducible —
   not a probabilistic model judging itself.
2. **Tamper-evident audit logs.** Every decision is recorded to an
   append-only JSONL log. A signed variant (HMAC-SHA256 + hash chain)
   makes after-the-fact deletion or modification detectable.
3. **An organisation-owned policy.** The policy is a human-readable file in
   your repository, reviewed and version-controlled like any other code.

Aigis runs entirely locally and adds no new runtime dependencies. It does
not send your prompts or code anywhere; it governs what the agent is
allowed to do on your machine.

## What this pack contains

- **Control matrix** — Aigis controls mapped to ISO/IEC 27001:2022 Annex A,
  NIST AI RMF, OWASP LLM Top 10, and the METI/MIC AI Business Operator
  Guidelines v1.2, plus an explicit "what Aigis does NOT cover" boundary.
- **Policy snapshot** — the exact policy currently in force, in plain
  language and as literal YAML.
- **Audit log evidence** — where logs live, their schema, retention, the
  tamper-evidence design, and the command to verify integrity.
- **Incident runbook** — what happens when Aigis blocks an action, how to
  triage, escalate, and report false positives.
- **Rollout plan** — a three-phase pilot template with review gates.

## Current live posture

- **Policy profile:** Aigis Default Policy (v1.0), 16
  rules — 10 deny, 5 review, 1 allow.
  Default decision when no rule matches: `allow`.

  **Read this before approving.** The rule set is a **deny-list**: it enumerates
  known-dangerous operations (recursive deletion, raw disk writes, credential and
  SSH-key access, piping a download into a shell) and lets everything else
  proceed — an agent that cannot run `ls` is not usable. So the default above is
  **fail-open by design, not by oversight: an operation nobody wrote a rule for
  will run.** If your review requires the opposite posture — deny unless
  explicitly permitted — set `default_decision: deny` in `aigis-policy.yaml` and
  add allow rules for the operations your team actually needs. That is a real
  piece of work, and it is the honest price of a fail-closed configuration.

  The policy name above comes from the policy file itself. If it was produced by
  `aigis profile build`, the capability combination behind it decides the rules —
  and the rules, not the name, are what section 3 sets out in full. Judge the
  configuration by those.
- **Hook status:** installed and configured.
- **Log status:** no events recorded yet.
- **Signed audit log:** enabled.
- **SIEM forwarding:** not detected (forwarders are configured in code; see docs/forwarders.md).


