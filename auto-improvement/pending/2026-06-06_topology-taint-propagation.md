# Pending: Topology External-Input Taint Propagation

- **Title**: Topology-level taint tracking for TOMA / OMNI-LEAK cascade attacks
- **Motivation**: Per-message injection detection misses topology-aware multi-hop cascade attacks (TOMA, arxiv:2512.04129) and orchestrator-induced data leakage via access control bypass (OMNI-LEAK, arxiv:2602.13477). An attacker injects into a low-privilege peripheral agent; the payload then propagates hop-by-hop toward high-privilege central agents via normal delegation.
- **Research finding**: TOMA achieves 40–78% ASR across three MAS frameworks; 85% against real applications. OMNI-LEAK shows that even properly access-controlled sub-agents become exfiltration sources when the orchestrator synthesizes their outputs.
- **Proposed change**: Extend `aigis/multi_agent/topology.py` `AgentTopology`:
  1. Add an `external_taint` flag per agent that is set when `record_communication` is called after a message with risk score > threshold from an external/tool source.
  2. `record_communication()` returns an anomaly flag when: `privilege(to_agent) > privilege(from_agent)` AND `from_agent.external_taint == True`.
  3. `summary()` reports `tainted_upward_delegations` count.
- **Why held back**: This touches `topology.py` with algorithmic logic changes (not just additive patterns), risk of affecting existing behavior, and the scope exceeds a clean 100 LOC non-test diff.
- **Constraint**: Would likely touch >50 LOC in topology.py plus test additions. Requires careful consideration of how taint propagates and when it expires.
- **Suggested next step**: Dedicate a `multi-agent` cycle to this change alone. Design the taint expiry window (N turns) and privilege comparison logic before implementing.
