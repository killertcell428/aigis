# Pending: Tool Chaining Sequence Detection in AgentTopology

## Title
Topology-level tool-call sequence analysis for illegitimate tool chaining

## Motivation
AgentLAB (arxiv:2602.16901, Feb 2026) and MASpi (OpenReview 2026) both document "tool chaining"
as a distinct attack type: individually-authorized tool calls are sequenced in a way that achieves
an illegitimate outcome. Example: an agent is authorized to read files, encode data as base64,
and POST data to a webhook — but only for specific legitimate purposes. An attacker injects a
message that triggers this sequence against sensitive files, achieving data exfiltration without
any single tool call being unauthorized.

## Which research finding led to this
AgentLAB (arxiv:2602.16901) — defines tool chaining as "sequencing multiple legitimate tools to
achieve an illegitimate outcome." Also relevant: multi-hop cascade attack research
(arxiv:2512.04129) showing that topology-aware attacks compound across hops. Research cycle:
2026-06-06T09-09 (domain: multi-agent).

## Proposed change
Extend `AgentTopology` with a tool-call sequence tracker:

1. Record not just edge frequency but also the sequence of tool types on each edge
   (e.g., [read_file → encode_base64 → http_post]).
2. Maintain a configurable list of "risky sequences" — predefined patterns of tool types that
   together constitute a high-risk chain.
3. `topology.check_sequence_risk(edge)` returns a risk score if the most recent N tool calls
   on that edge match a known risky pattern.

## Why it was held back
- Adding sequence tracking to `AgentTopology` would require changes to both `topology.py` and
  its public API, exceeding 100 LOC and potentially breaking the API surface.
- The "risky sequence" list must be configurable by users, requiring a new configuration schema.

## Which constraint blocked it
100 LOC limit; also potential public API change (adding fields to `AgentTopology.summary()`
and new `check_sequence_risk()` method).

## Suggested next step for human reviewer
1. Design the `ToolCallSequence` data model and `check_sequence_risk()` API.
2. Implement the predefined risky-sequence list as a YAML config under `policy_templates/`.
3. Add integration tests using the AgentLAB tool-chaining test cases.
4. Consider making this an opt-in `AgentTopology(track_sequences=True)` flag to avoid
   breaking existing users.
