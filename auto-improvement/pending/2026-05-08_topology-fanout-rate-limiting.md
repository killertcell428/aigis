# Pending: Fan-Out Rate Limiting in AgentTopology for Cascade Detection

**Date:** 2026-05-08  
**Cycle:** 6 (multi-agent)  
**Research finding:** OWASP ASI-08 (Cascading Failures, 2026) — a single agent-level fault can fan out across all downstream agents when no message rate cap exists. Microsoft's Copilot Studio guidance (March 2026) explicitly recommends circuit breakers and fan-out caps.

## Motivation

`AgentTopology` currently tracks communication edges and computes `unexpected_edges()` but does not limit or alert on the *rate* of message fan-out. An attacker who triggers a cascade can cause one compromised agent to spam instructions to 50 downstream agents within milliseconds, each of which amplifies the effect further.

## Proposed change

Add `AgentTopology.set_fanout_cap(from_agent: str, max_per_second: int)` and a per-edge rolling counter that raises `CascadeWarning` (or returns it in `summary()`) when the cap is exceeded. No external dependencies required — use a simple sliding-window counter with `time.monotonic()`.

Extend `MessageScanResult` with a `cascade_risk: bool` field set by a new `scan_with_topology()` convenience method.

## Why held back

**Constraint: > 100 LOC change.** The rolling counter logic + `CascadeWarning` + `scan_with_topology()` + tests would be ~130–150 LOC across non-test files. Also, changing `MessageScanResult` is a public API extension (not breaking, but requires care to not break existing dict serialization tests).

## Suggested next step

Implement in a dedicated cycle as `AgentTopology` enhancement only (no change to `MessageScanResult`). The topology-side change alone is ~60 LOC + ~30 LOC tests = 90 LOC total — fits under the limit.
