# Pending: Agent Identity Spoofing via Forged `from_agent` Field

**Date:** 2026-05-08  
**Cycle:** 6 (multi-agent)  
**Research finding:** arxiv:2506.19676 (LLM Agent Communication survey, 2026) — "agent spoofing" involves forging the sender identity in A2A protocol messages; cross-organization agent calls make trust boundaries extremely wide.

## Motivation

In multi-agent systems, the `AgentMessage.from_agent` field is currently accepted at face value. An attacker who can inject a single inter-agent message can set `from_agent="orchestrator"` and claim orchestrator-level authority, bypassing trust-differential checks in `AgentTopology`. TAMAS impersonation attacks that reached 82% ASR rely on exactly this mechanism.

## Proposed change

Add optional cryptographic signing support to `AgentMessage`:
- A `signature` optional field (HMAC-SHA256 over `from_agent + to_agent + content + timestamp`).
- `AgentTopology.verify_sender()` method that checks the signature against a registered public key or shared secret for each agent.
- `AgentMessageScanner` to optionally call `verify_sender()` when a `topology` is provided.

This would convert `from_agent` from an advisory field to a cryptographically verifiable claim.

## Why held back

**Constraint: breaking public API change.** Adding a mandatory `signature` field would break all existing callsites that construct `AgentMessage` without it. Making it optional is feasible, but the `AgentTopology.verify_sender()` integration touches the public API of both `AgentMessageScanner` and `AgentTopology`, and the total diff would exceed 100 LOC across non-test files. Additionally, requiring a shared-secret management system could be perceived as adding a "required runtime dependency" (key store), though an in-memory dict is zero-dependency.

## Suggested next step

Implement as an opt-in parameter `AgentMessageScanner(verify_signatures=False)` in a dedicated cycle. The diff for the scanner + topology side is ~80 LOC; add tests for ~40 LOC (total ~120, so spans two cycles or requires relaxing the 100 LOC limit for a single well-scoped hardening).
