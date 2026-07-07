---
title: "Your company won't approve Claude Code? I built an open-source trust layer for that"
tags: [claudecode, security, opensource, ai]
published: false
# canonical_url: https://dev.to/killertcell428/your-company-wont-approve-claude-code-i-built-an-open-source-trust-layer-for-that
---

## The shadow AI trap

Here's a pattern I've been watching play out across engineering teams:

A developer discovers Claude Code. Productivity goes up measurably — not the "I think it helps" kind, the "I shipped in 2 days what used to take 2 weeks" kind. They tell their team. Then someone asks the question that kills the momentum: "Did IT approve this?"

Two paths open up. Path one: submit a request to the security team, wait months, get a "we need more information" reply, wait more months. Path two: quietly keep using it and hope nobody notices.

Neither is good. Path one blocks the productivity gain indefinitely. Path two creates shadow AI exposure that real incident response teams have to deal with after the fact. The security team isn't being obstructionist — they're asking legitimate questions that currently have no structured answer.

I've been thinking about how to fix path one instead of working around it.

---

## What IT security actually needs

When a security team reviews a new developer tool — especially one that can execute shell commands, write to the filesystem, and call external APIs — the questions they ask are reasonable:

- What actions can it take, and what are the boundaries?
- Where do audit logs go, and are they tamper-evident?
- Which compliance frameworks does this map to? (ISO 27001, NIST AI RMF, OWASP LLM Top 10)
- What's the incident response procedure?
- Is there a phased rollout plan?

The problem with Claude Code isn't that it fails these checks. It's that there's no pre-packaged way to answer them. The approval conversation becomes a bespoke, slow, person-dependent process every single time.

There's also a specific gap worth naming: Claude Code's Enterprise plan exports OpenTelemetry telemetry, which is useful for operational observability. But OTel telemetry isn't an audit trail — it doesn't carry tamper-evidence, doesn't maintain a hash chain, and wasn't designed to answer "prove this log hasn't been modified." For compliance reviews that require audit-grade evidence, this gap matters.

---

## Why independent OSS matters right now

If you've been tracking the AI security tooling space, you may have noticed something: every major independent tool in this category got acquired in the past year.

- Protect AI → Palo Alto Networks (July 2025)
- Invariant's mcp-scan → Snyk (June 2025)
- Lakera → Check Point (2025)
- promptfoo → OpenAI (March 2026)

Each acquisition makes sense commercially. But from an enterprise security perspective, vendor lock-in to an AI provider's own audit tooling creates a conflict of interest problem. If OpenAI owns your Claude Code audit tool, or Palo Alto's commercial incentives drive feature decisions, you've traded independence for integration convenience.

Aigis is Apache-2.0, zero-dependency, deterministic (no API calls, $0 marginal cost), and auditable in its own right. It will stay independent.

---

## The two-layer model

Before getting to the demo, the architecture matters for understanding why this approach works.

**Layer 1 — Claude Code's own enterprise controls**

Claude Code's Team and Enterprise plans support `managed-settings.json` distributed via MDM. This lets your org define which commands are allowed, which permissions are granted, and what the defaults are. This is a real, meaningful control layer. Aigis does not replace it — it treats it as the foundation.

**Layer 2 — Aigis PreToolUse hooks + signed audit log**

`aigis init --agent claude-code` installs `.claude/hooks/aig-guard.py` into your project. Before Claude Code executes any tool, this hook runs the action through Aigis's policy engine. If the action doesn't pass policy, execution stops before it happens.

Every decision — allowed, blocked, or flagged — gets written to an audit log protected by HMAC-SHA256 signatures and a SHA-256 hash chain. The chain links every entry to the previous one; any modification breaks the chain, which `aigis audit verify` will detect.

Neither layer alone is sufficient. Layer 1 without layer 2 has no audit-grade logging. Layer 2 without layer 1 has weaker enforcement at the source. Together, they answer most of what an IT security team needs to see.

---

## The trust-pack demo

Here's what the approval workflow looks like in practice:

```bash
# Step 1: install
pip install 'pyaigis[all]'

# Step 2: initialize with enterprise policy + Claude Code hooks
aigis init --agent claude-code --policy enterprise

# Step 3: generate the bilingual IT-approval document pack
aigis trust-pack --lang both --format html

# Step 4: open it
open aigis-trust-pack/index.html
```

What gets generated:

```
aigis-trust-pack/
├── index.html                    # navigable entry point
├── executive-summary.ja.md       # Japanese exec summary (for 情シス)
├── executive-summary.en.md       # English version
├── control-matrix.md             # ISO 27001 / NIST AI RMF / OWASP / METI mapping
├── policy-snapshot.yaml          # exact current aigis-policy.yaml contents
├── audit-log-spec.md             # HMAC + hash-chain spec with sample entries
├── incident-runbook.md           # incident response procedure
└── rollout-plan.md               # pilot → department → org-wide plan
```

The control matrix maps each security requirement to three columns: what Claude Code's own controls provide (layer 1), what Aigis adds (layer 2), and what the organization still needs to decide (marked `[TO FILL]`). The `[TO FILL]` fields are intentional — Aigis generates evidence, not decisions.

---

## MCP supply-chain risk: rug-pulls and tool poisoning

If you're using Claude Code with third-party MCP servers, there's an additional attack surface. MCP tool definitions can change after you've reviewed them (rug-pull), or contain hidden instructions embedded in descriptions (tool poisoning — this class of attack is documented in Invariant's research and the OWASP LLM Top 10).

```bash
# scan an MCP tool definition + check trust score + diff against last snapshot
aigis mcp --file .claude/mcp_tools.json --trust --diff
```

Aigis snapshots tool definitions on first scan. On subsequent runs, `--diff` flags any changes for review.

---

## Verifying the audit log

The tamper-evidence property is only useful if it's verifiable. Here's what verification looks like:

```bash
aigis audit verify

# Output:
# chain_valid: true
# signature_valid: true
# 1,247 entries checked
# 0 entries with broken chain
# 0 entries with invalid signatures
```

If a log file gets modified — even a single character change — the chain breaks and `audit verify` reports the sequence number of the first broken link.

For teams running a SOC, all events can forward in real time to Splunk, Datadog, Microsoft Sentinel, or Elastic via the SIEM forwarder module.

---

## Honest limits

I want to be precise about what this does and doesn't do, because overclaiming is how security tools lose credibility:

**What Aigis does:**
- Deterministic, pattern/policy-based detection — no API calls, no external dependencies, auditable logic
- Tamper-evident audit logs with HMAC signatures and SHA-256 hash chains
- Auto-generated compliance mapping documents for ISO 27001, NIST AI RMF 1.0, OWASP LLM Top 10 2025, and Japan METI AI Business Operator Guidelines
- SIEM forwarding to four major platforms
- MCP supply-chain scanning with diff-based change detection

**What Aigis does not do:**
- Control what happens inside Anthropic's cloud (model inference is outside this boundary)
- Catch novel attacks that don't match any known pattern
- Make your organization "ISO 27001 compliant" — it generates evidence; certification requires a full ISMS
- Make the `[TO FILL]` organizational decisions for you

Aigis is a defense-in-depth layer. It works best as part of a real security program, not as a substitute for one.

---

## Try it

```bash
pip install 'pyaigis[all]'
aigis init --agent claude-code --policy enterprise
aigis trust-pack --lang both --format html
```

GitHub: https://github.com/killertcell428/aigis
Adoption guide: `docs/adoption/`
46 stars and climbing — if this is useful, a star helps more engineers find it.

If you've been through a corporate AI tool approval process — successfully or not — I'd genuinely like to hear what the sticking points were. Open an issue or drop a comment.
