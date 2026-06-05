# Pending: Promptware Lateral Movement Forwarding Detection

**Date:** 2026-06-05
**Domain:** multi-agent (cycle 6)
**Research basis:** "The Promptware Kill Chain" (arxiv:2601.09625, January 2026)

---

## Title

Detect lateral movement forwarding directives in inter-agent messages

## Motivation

The Promptware Kill Chain (arxiv:2601.09625) documents 21 of 36 real prompt injection incidents traversing ≥4 kill chain stages. Stage 6 (Lateral Movement) is detectable when an agent sends another agent instruction-carrying relay commands:

- "repeat this to your colleagues"
- "pass this instruction to the next agent"
- "tell the next agent that your new task is [malicious instruction]"

These are distinct from the existing `_SELF_REPLICATION_PATTERNS` (which target "embed in every response" instructions) and `_DELEGATION_PATTERNS` (which target impersonation claims). Lateral movement forwarding explicitly names a downstream agent or role as the target of an instruction payload.

## Proposed change

Add `_LATERAL_MOVEMENT_PATTERNS` to `aigis/multi_agent/message_scanner.py`:

```python
_LATERAL_MOVEMENT_PATTERNS = [
    (
        re.compile(
            r"(pass|relay|forward|send)\s+(this\s+)?(instruction|directive|command|task|goal|objective)"
            r".{0,30}(to\s+(the\s+)?(next|downstream|other|following)\s+(agent|node|worker|assistant))",
            _FLAGS,
        ),
        "Lateral movement: instruction payload directed at downstream agent",
        "injection_relay",
    ),
    (
        re.compile(
            r"(tell|inform|instruct|notify)\s+(the\s+)?(next|downstream|other|following)\s+"
            r"(agent|node|worker|assistant).{0,30}(your\s+new\s+(task|goal|objective)\s+is|now\s+do|execute)",
            _FLAGS,
        ),
        "Lateral movement: goal/task override forwarded to downstream agent",
        "injection_relay",
    ),
    (
        re.compile(
            r"repeat\s+this.{0,30}(to\s+(your\s+)?(colleague|peer|other|fellow)\s+(agent|node|worker))",
            _FLAGS,
        ),
        "Lateral movement: instructs repeating payload to peer agents",
        "injection_relay",
    ),
]
```

## Why held back

The first pattern partially overlaps with the existing `_DELEGATION_PATTERNS` relay pattern ("forward/relay/pass/send this/these/the following to"). Need to audit for false positive and deduplication before implementing. Requires a dedicated test class with negative cases to avoid regression.

## Constraint blocking

LOC budget consumed by `_CAPABILITY_SCOPE_INFLATION_PATTERNS` and `_BYZANTINE_CONSENSUS_PATTERNS` this cycle. Overlap analysis with `_DELEGATION_PATTERNS` needs review.

## Suggested next step

Implement in the next multi-agent cycle (index 6). First, audit `_DELEGATION_PATTERNS` pattern 3 (forward/relay/pass this to) to check for overlap. If partial overlap, consolidate or add complementary coverage. Add test class `TestLateralMovement` with 4 cases covering the three patterns plus one safe benign message.
