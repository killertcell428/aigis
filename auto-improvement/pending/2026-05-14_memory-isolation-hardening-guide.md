# Pending: Cross-Session Memory Isolation Hardening Guide

**Title:** Cross-Session Memory Isolation Hardening Guide

**Motivation:**
The `arxiv:2503.16248` (March 2026) paper on Web3 agent memory attacks documents cross-session backdoors: a malicious memory entry planted by one user persists in a shared memory store and activates in another user's session. This is a user-to-user attack path unique to multi-tenant agent deployments. Operators running shared or multi-tenant agent services need practical guidance on how to isolate memory namespaces and prevent cross-session contamination.

**Which research finding led to this:**
- arxiv:2503.16248 ("Real AI Agents with Fake Memories") — cross-session backdoor section
- General principle: memory stores are often shared across users in multi-tenant deployments without namespace isolation

**Proposed change:**
Add `docs/hardening/memory_isolation.md` covering:
1. Memory namespace isolation: each user/session should have a fully isolated memory namespace; no sharing of long-term memory between users by default
2. Write-time and read-time scanning: memory should be scanned with aigis on both write (before persisting) and read (before presenting to the model), not only at ingestion
3. Provenance tagging: memory entries should carry a trusted source identifier (user ID, session ID, timestamp) and entries from external/tool sources should be tagged accordingly
4. Retention limits: poisoned entries persist indefinitely without TTL; recommend TTL policies for long-term memory entries
5. Cross-session isolation test cases: examples using aigis's scanner to validate that memory stores are properly namespaced

**Why it was held back:**
Exceeds the 100 LOC non-test diff limit. A thorough hardening guide would be 150-200 LOC of documentation plus example code snippets. Splitting it into pieces smaller than the natural unit would reduce its usefulness.

**Which constraint blocked it:**
> Any single change touching > 100 LOC across non-test files

**Suggested next step for human reviewer:**
Implement `docs/hardening/memory_isolation.md` in a dedicated cycle focused on documentation hardening (domain index 4 or 8). The guide should include code examples showing how to integrate aigis's scanner into memory write and read paths.
