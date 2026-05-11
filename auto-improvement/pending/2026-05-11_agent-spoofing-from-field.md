# Pending: Agent Identity Spoofing via Forged `from_agent` Field

**Title:** Metadata-layer sender validation for A2A messages

**Motivation:**
A2A session smuggling and agent impersonation attacks are much easier when an attacker can forge the `from_agent` field in `AgentMessage`. Content scanning catches injected text, but a malicious agent that claims to be the orchestrator at the metadata level (not just in message content) can bypass all content-based patterns.

**Research finding that led to this idea:**
- Agent Session Smuggling (Unit42, April 2025): the attack exploits implicit trust in sender identity within stateful A2A sessions.
- TAMAS benchmark (arxiv:2511.05269, ICML 2025): impersonation attacks reached 82% ASR in Swarm configurations.
- A Survey of LLM-Driven Agent Communication (arxiv:2506.19676, 2026): agent spoofing (forging the `from_agent` field) is explicitly listed as an attack vector.

**Proposed change:**
Add an optional `allowed_senders` dict to `AgentMessageScanner` (or a separate `AgentIdentityValidator` class) that maps agent IDs to expected trust levels. When a message arrives with `from_agent="orchestrator"` but the sender is not in the allowlist, flag it as `privilege_escalation` with score 50. The check should be opt-in (default: no enforcement) to preserve backward compatibility.

**Why it was held back:**
- Requires non-content metadata validation, which is outside the current pure content-scanning architecture.
- An allowlist requires configuration by the user (they must register known agent IDs), adding API surface that needs careful design.
- Implementing correctly without breaking existing users needs a larger design decision (not a ≤ 100 LOC additive change).

**Constraint that blocked it:** Would touch public API surface area (AgentMessageScanner constructor) and likely exceed 100 LOC including tests and docs.

**Suggested next step for human reviewer:** Design a `from_agent` allowlist / trust-level enforcement option in `AgentMessageScanner.__init__()` with `known_agents: dict[str, str] | None = None` parameter. When provided, verify that `message.from_agent` is in the dict before trusting the content scan result.
