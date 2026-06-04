# Pending: OMNI-LEAK Cross-Agent Data Aggregation Patterns

**Title:** Detect cross-agent data aggregation instructions targeting the orchestrator architecture
**Motivation:** OMNI-LEAK (arxiv:2602.13477, 2026) demonstrates that a single indirect prompt injection in an orchestrator-based multi-agent system can cause multiple specialized sub-agents to collectively leak sensitive data that no single agent could access alone. The attack works by instructing the orchestrator to aggregate results from sub-agents beyond their access-controlled scope.

**Research finding:** arxiv:2602.13477 — "OMNI-LEAK: Orchestrator Multi-Agent Network Induced Data Leakage" (2026). Both reasoning and non-reasoning frontier models are vulnerable. Per-agent access controls are insufficient when the orchestrator can be instructed to synthesize sub-agent outputs.

**Proposed change:** Add patterns to `AgentMessageScanner` detecting:
- "collect (all|every) (results|data|output) from (all|every|the other) (agents|workers|nodes)"
- "aggregate (the|all) (results|data|information) from (all|every|each) (agent|sub-agent|worker)"
- "combine (the output|results) of (all|every|each) (agent|worker) into (one|a single) (response|report|output)"

**Why held back:** These patterns describe normal orchestrator behavior in multi-agent systems — an orchestrator legitimately aggregates sub-agent results to complete a task. The distinguishing factor in OMNI-LEAK is that the aggregation is being instructed by an untrusted external source (injected into a tool result) rather than by the system's own workflow definition. A regex alone cannot distinguish legitimate vs. adversarial aggregation instruction sources.

**Constraint that blocked it:** High FP risk in legitimate orchestrator workflows. The attack's distinguishing feature is context-of-origin (injected vs. designed), which is not captured in message content alone.

**Suggested next step:** Add a `message_source` field to `AgentMessage` to distinguish designed orchestration from externally-sourced aggregation directives. Pattern matching on aggregation language would be appropriate only when `message_source == "tool_result"` or `"external_content"`.
