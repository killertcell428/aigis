# Pending: ZombieAgent Memory Persistence Hardening Guide

**Date:** 2026-06-06
**Domain:** multi-agent (cycle 6, fourth pass)
**Research basis:** Radware ZombieAgent Advisory (January 2026); arxiv:2602.15654 (Zombie Agents)

---

## Title

Documentation guide: defending against zero-click persistent memory hijacking in agent deployments

## Motivation

The ZombieAgent attack (Radware, January 2026) demonstrated that when an AI agent with enterprise
data connectors (Google Drive, OneDrive, GitHub, Slack, Jira) autonomously reads external content,
a malicious document can cause the agent to (1) exfiltrate user data to an attacker-controlled
endpoint and (2) write a persistent malicious directive into its long-term memory store. The agent
then acts as a "zombie" — executing attacker goals on all future invocations without further
attacker input, even after conversation resets.

This attack is not detectable by input regex alone: the injected payload arrives as legitimate
document content, and the exfiltration step uses internal API calls rather than user-visible output.
A hardening guide documenting architectural defenses is more appropriate than a detector rule.

## Proposed change

Write `docs/hardening/zombie-agent-memory-persistence.md` covering:

1. **What the attack is** — plain-language explanation of zero-click persistent injection
2. **Why it matters for enterprise deployments** — connector surface area, memory persistence
3. **Architectural defenses:**
   - Memory write auditing: log every memory-write operation with the source document/URL
   - Memory isolation: separate write channels for user-instruction memory vs. autonomous agent memory
   - Connector content sanitization: pass retrieved connector content through aigis before agent processing
   - Memory TTL and expiry: automatically expire memory entries older than a configurable threshold
   - Human-in-the-loop for memory writes: require explicit user confirmation before persisting agent-generated memory entries
4. **aigis integration points:** how to wire the RAG context filter and memory module to screen connector content
5. **Detection indicators:** log patterns that suggest a ZombieAgent-style persistence attack is underway

## Why held back

Documentation-only change; not complex. Held back because the cycle's LOC budget and focus were
consumed by the `_CAPABILITY_SCOPE_INFLATION_PATTERNS` implementation.

## Constraint blocking

Not blocked by a hard constraint — capacity constraint only.

## Suggested next step

Implement in the next memory-context or multi-agent cycle. No code changes required; approximately
60–80 lines of Markdown.
