# Pending: Back-Reveal Behavioral Monitoring (Memory-Tool Exfil Chain)

**Date:** 2026-05-20
**Domain:** data-exfiltration (cycle 2, fifth pass)
**Research basis:** `research/2026-05-20T09-00_2-data-exfiltration.md`

---

## Title

Runtime behavioral monitoring for memory-access tool calls followed by external URL egress
(Back-Reveal attack pattern)

## Motivation

The Back-Reveal paper (arxiv:2604.05432, April 2026) documents a backdoored fine-tuning
attack where semantic triggers cause an LLM agent to:
1. Invoke memory-access tool calls (`retrieve_memory`, `search_docs`, `get_context`)
2. Silently base64url-encode session memory into a URL query parameter
3. Exfiltrate the encoded data to an attacker-controlled retrieval endpoint disguised as a
   legitimate tool response

Multi-turn impact: attacker-controlled retrieval responses steer subsequent agent behavior.
Attack success: 87% single-turn, >97% with majority voting across three generations.
Bypasses: NeMo Guardrails, LLM Guard, and reranker-based filtering — all fail because they
inspect retrieval *content* not *tool-call payload structure*.

## Proposed Change

This is NOT addressable by a static regex pattern (the trigger is embedded in model weights).
The correct mitigation is runtime behavioral monitoring:

1. **Tool call sequence auditing**: Flag any multi-turn session where a memory-access tool call
   (`retrieve`, `memory`, `recall`, `search_docs`) is immediately followed (within the same
   turn) by an outbound HTTP call or external URL in the response.

2. **Base64url payload detection in tool call arguments**: Flag tool call arguments that contain
   long base64url-encoded strings (40+ chars, URL-safe alphabet: `[A-Za-z0-9_-]`) passed as
   URL query parameters.

This would require a new detection layer beyond pattern-matching: turn-level behavioral
analysis across the tool call sequence, not a single-turn regex scan. This is architecturally
different from aigis's current static-pattern approach.

## Why Held Back

1. **Architecture mismatch**: Static regex applied to a single text does not have access to
   multi-turn tool call history. Implementing this requires either:
   - A stateful session monitor that tracks tool call sequences
   - Or a heuristic that fires on a single turn: `retrieve_memory(..)` in the same response
     as a URL with a long base64url parameter
   
2. **FP risk**: Base64url-encoded strings of 40+ chars appear legitimately in OAuth tokens,
   JWT authorization headers, and other technical contexts.

3. **Non-trivial implementation**: Would require changes to the session tracking layer
   (`aigis/cross_session/`) or a new stateful scanner, not just a pattern addition.

## Suggested Next Step for Human Reviewer

1. Consider adding a heuristic output rule that flags the combination of:
   - A tool call name containing `memory`, `retrieve`, `recall`, or `search_docs`
   - AND a URL in the same response containing a base64url payload 40+ chars
   This would be a single-turn proxy for the behavioral signal.
2. Or extend `cross_session/correlator.py` with a pattern that fires on the tool-call
   sequence across turns.
3. Sources:
   - https://arxiv.org/abs/2604.05432
   - https://arxiv.org/abs/2604.03070
