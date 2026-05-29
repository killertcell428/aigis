# Pending: Novel Custom Cipher Behavioral Detection

**Date:** 2026-05-29
**Cycle:** 3 (jailbreak-extraction fourth pass)
**Research source:** Research file `2026-05-29T06-00_3-jailbreak-extraction.md`

---

## Motivation

MetaCipher (arxiv:2506.22557, Jun 2025) demonstrates a multi-agent framework where an orchestrator
LLM autonomously generates novel, dynamically-rotating cipher schemes and teaches them to target
LLMs in-context. This is more effective than known named ciphers (ROT13, Caesar) because static
regex detection based on cipher names does not cover dynamically invented schemes. MetaCipher
achieves time-persistent jailbreaks by negotiating the cipher across sessions.

Handa et al. (arxiv:2402.10601) similarly showed that novel user-defined ciphers outperform
widely studied ciphers, with 70-90% ASR on GPT-4 and Claude-2.

## Why Regex Cannot Fully Address This

A novel cipher is definitionally novel — there is no fixed name to match. Detection requires one
of:
1. Semantic analysis of the content (does it contain a jailbreak intent when decoded?)
2. Behavioral analysis (does the model's response show anomalous patterns consistent with cipher
   output?)
3. Statistical analysis (does the input contain an unexpectedly high density of rare character
   sequences or letter substitution patterns?)

None of these are achievable with a simple regex in aigis's current architecture.

## Proposed Change

This is a roadmap item for the cross-session behavioral correlator. When aigis gains a behavioral
analysis layer, it should check:

1. **In-context cipher definition**: User messages that define a substitution table or encoding
   rule followed by a harmful topic request.
2. **Response entropy anomaly**: Unusually high character-frequency entropy in model responses
   (compared to natural language baseline) indicating cipher encoding.
3. **Session-level cipher negotiation**: Multi-turn patterns where early turns establish an
   encoding scheme before later turns make harmful requests.

## Constraint

Requires a semantic/behavioral analysis layer beyond regex scope. Cannot be implemented as a
`DetectionPattern` in the current architecture without false positive rates that would make the
filter unusable.

## Suggested Next Step

When the cross-session behavioral correlator feature is designed, add detection for in-context
cipher-definition patterns (step 1 above) as the first tractable sub-goal. Specifically: input
contains a custom substitution mapping table (e.g., "A=X, B=Y...") followed by a harmful request.
This IS regex-detectable and would catch a specific variant of MetaCipher attacks.
