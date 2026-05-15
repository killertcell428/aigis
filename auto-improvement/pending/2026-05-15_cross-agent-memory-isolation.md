# Pending: Cross-Agent Memory Isolation Audit Helper

## Title
Cross-agent memory isolation audit helper in the `memory/` module

## Motivation
The Unintentional Cross-User Contamination (UCC) paper (arxiv:2604.01350, April 2026) found that under raw shared agent state, benign multi-agent interactions alone produce 57–71 % contamination rates across users and sessions, with no malicious actor required. A single poisoned memory object spread across sessions, users, and sub-agents, with one compromised agent poisoning 87 % of downstream decisions within 4 hours in simulated systems.

This demonstrates that memory isolation is a **safety requirement**, not just a privacy requirement. Contamination at this rate means that even without an adversary, production multi-agent deployments may silently corrupt future agent behavior.

## Which research finding led to this idea
Research file: `auto-improvement/research/2026-05-15T03-02_6-multi-agent.md`
Finding: "Unintentional cross-user contamination — 57–71 % contamination rate with no attacker required" (arxiv:2604.01350)

## Proposed change
Add a `MemoryIsolationAuditor` class (or extend existing `memory/` module) that:
1. Checks whether memory objects are namespaced per user/session
2. Detects attempts to read memory across user or session boundaries
3. Flags memory write operations that lack a session identifier
4. Logs cross-boundary memory access attempts

Optionally, add detection rules for content patterns that suggest cross-session context leakage ("in our previous session, the user mentioned that…" in a context where the session should be fresh).

## Why it was held back
- The `memory/` module would require > 100 LOC of new non-test code to implement meaningfully
- The change touches memory read/write semantics, which is a behavioral change requiring careful testing
- This exceeds the single-cycle "≤ 100 LOC non-test diff" constraint

## Which constraint blocked it
Hard constraint: "Any single change touching > 100 LOC across non-test files" → send to pending.

## Suggested next step for the human reviewer
1. Review the UCC paper (arxiv:2604.01350) for specific contamination vectors
2. Design the `MemoryIsolationAuditor` interface as a standalone class in `aigis/memory/`
3. Implement in a dedicated cycle with expanded LOC budget, with tests covering:
   - Cross-user memory reads (should be flagged)
   - Missing session namespacing (should warn)
   - Legitimate same-session memory access (should not be flagged)
