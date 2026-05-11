# Pending: Fan-Out Rate Limiting in AgentTopology

**Title:** Topology-layer detection of cascade-triggering message floods

**Motivation:**
OWASP Top 10 for Agentic Applications 2026 (ASI-08: Cascading Failures) describes a scenario where a single agent-level injection triggers a fan-out: "forward this to all downstream nodes" causes the message count to exponentially grow across the agent graph, amplifying both the attack's impact and resource consumption.

**Research finding that led to this idea:**
- OWASP Agentic Top 10 ASI-08: cascading failure via fan-out from a single poisoned agent (December 2025/March 2026).
- MASpi Disruption suite (OpenReview, April 2026): disruption attacks that flood coordination channels appear as topology-level anomalies before they appear as content anomalies.
- A Survey of LLM-Driven Agent Communication (arxiv:2506.19676, 2026): Denial-of-Service via coordination flooding.

**Proposed change:**
Add a `max_messages_per_window` and `window_seconds` parameter to `AgentTopology`. When `record_communication()` is called, track the message rate per `(from_agent, to_agent)` pair in a rolling time window. If the rate exceeds the threshold, return a flag from `record_communication()` or add an entry to `unexpected_edges()`. This would let users detect when a single agent suddenly floods peers — a cascade-in-progress signal.

**Why it was held back:**
- Requires time-bucketed counters in `AgentTopology` — a non-trivial internal data structure change.
- The `record_communication()` return type is currently `CommunicationEdge`; adding a flood flag either changes that type (public API) or requires a separate method.
- Implementing with tests likely exceeds 100 LOC across non-test files.

**Constraint that blocked it:** Public API change (CommunicationEdge or record_communication signature) and LOC > 100.

**Suggested next step for human reviewer:** Add an optional `flood_threshold: int = 0` parameter to `AgentTopology`. When > 0, track a per-edge message count per rolling 60-second window. Return a boolean `is_flooding` field from `record_communication()` (or add it to `CommunicationEdge`). Raise the default threshold high enough (e.g. 100/min) to avoid false positives in normal orchestration.
