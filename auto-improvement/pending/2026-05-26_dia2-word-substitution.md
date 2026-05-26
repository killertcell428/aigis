# Pending: DIA-II Word-Substitution Extraction Probe

**Date:** 2026-05-26
**Cycle:** 4 (jailbreak-extraction fourth pass)
**Research source:** Research file `2026-05-26T06-17_3-jailbreak-extraction.md`

---

## Motivation

arxiv:2503.08195 (Meng et al., March 2025) describes DIA-II as an extension of DIA-I
(affirmative prefill, already implemented as `jb_affirmative_prefill`). DIA-II injects a fake
prior assistant turn containing a partial harmful response, then asks the model to perform
word substitution ("replace X with Y in your previous answer") to extract the full content
indirectly. It achieves higher ASR than DIA-I in black-box API settings.

Detectable pattern:
```
(replace|substitute|swap|change).{0,40}(word|term|phrase).{0,60}(previous|last|your|above).{0,30}(answer|response|message)
```

## Why Held Back

**False positive risk:** Legitimate writing assistants, grammar checkers, and editors routinely
request "replace this word in your previous answer." Without the injected harmful prefill in
context, the word-substitution phrase alone has high FP risk.

## Which Constraint

Exceeds the single-turn rule-based paradigm without context of the injected turn. Session-aware
detection or multi-message context scanning would be required to distinguish DIA-II from
legitimate editing requests.

## Suggested Next Step

Implement as a session-level correlator: flag word-substitution requests that arrive within N
turns of an affirmative-prefill-style injection. Requires the cross-session correlator
infrastructure already noted on the roadmap.
