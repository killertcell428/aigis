# Pending: LLM Router Response-Integrity Hardening Guide

## Title
Hardening guide for detecting and mitigating malicious LLM API router attacks

## Motivation
LLM API routers (middleware that routes requests to model providers) terminate TLS and have plaintext access to all JSON payloads. A malicious router can perform JSON-path mutation — silently rewriting tool call responses before they reach the client agent. Examples: substituting package names in install commands (`requests` → `reqeusts`), injecting credential-exfiltrating instructions into shell command outputs, or passively harvesting all credentials flowing through sessions. 9 of 428 tested public routers were actively injecting malicious content.

Because this attack operates at the infrastructure layer between the agent and the model provider, it cannot be detected by content-scanning the agent's messages or outputs alone — it requires architectural and operational controls.

## Research finding that led to this idea
`auto-improvement/research/2026-06-04T09-23_6-multi-agent.md` — arxiv:2604.08407 (Liu et al., UC Santa Barbara, April 2026): 100% ASR for shell command URL substitution across four tested frameworks (OpenClaw, OpenCode, Codex, Claude Code); 99 credentials extracted across 440 sessions; 2.1 billion billed tokens processed through poisoned chains. One "conditional warm-up" variant stays benign for 50+ calls to evade audit-based detection.
- Source: <https://arxiv.org/html/2604.08407v1>

## Proposed change
Create `docs/hardening/llm-router-supply-chain.md` containing:

1. **Threat model** — what LLM API routers can modify and why the attack is undetectable at the content layer
2. **Architectural controls** — use direct provider SDK connections rather than third-party routers when possible; prefer official SDKs with certificate pinning
3. **Response verification** — compare response schema against expected tool output structure; flag responses whose tool-call return values include command-line URLs or package names not matching a known allowlist
4. **Audit trail controls** — log all tool-call inputs and outputs including response metadata; look for content-length changes between expected and received responses
5. **Conditional warm-up evasion** — rotate audit queries; do not rely solely on the first N responses to verify router integrity
6. **Aigis integration points** — where to place aigis `Guard.check_output()` calls to scan tool responses for credential regex patterns (`AKIA[A-Z0-9]{16}`, `ghp_[A-Za-z0-9]{36}`, `sk-[A-Za-z0-9]{20,}`) that should not appear in normal tool outputs

## Why it was held back
This is a documentation/guidance deliverable, not a new detection rule. Writing a thorough hardening guide requires more space than the standard cycle commit allows cleanly. No code change is needed for this item — it is purely additive documentation.

## Which constraint blocked it
None hard — this is scope management. A docs-only cycle item is valid.

## Suggested next step for the human reviewer
Assign a docs-only cycle to write `docs/hardening/llm-router-supply-chain.md`. The content in "Proposed change" above is the outline. Cross-link from `docs/integrations/` and the README's security section.
