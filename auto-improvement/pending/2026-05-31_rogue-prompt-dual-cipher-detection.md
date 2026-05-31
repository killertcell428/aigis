# Pending: RoguePrompt Dual-Layer Cipher Detection

**Date:** 2026-05-31
**Cycle:** 3 (jailbreak-extraction fourth pass)
**Research source:** `research/2026-05-31T00-12_3-jailbreak-extraction.md`

---

## Motivation

arxiv:2511.18790 "RoguePrompt: Dual-Layer Ciphering for Self-Reconstruction to Circumvent LLM
Moderation" (November 2025) uses two sequential encoding layers — ROT-13 followed by a Vigenère
cipher — with embedded natural-language decoding instructions inside a single query. The attack
prompts the target model to decode and execute the hidden payload within one round-trip.

Evaluated on 313 real-world hard-rejected prompts across multiple frontier LLMs:
- Filter bypass rate: 93.93% (the encoded form evades surface scanners)
- Instruction reconstruction: 79.02%
- Execution success: 70.18%

## Proposed Change

Add `jb_dual_cipher_decode` to `JAILBREAK_ROLEPLAY_PATTERNS`:

```python
DetectionPattern(
    id="jb_dual_cipher_decode",
    name="Dual-Layer Cipher Jailbreak (RoguePrompt)",
    category="jailbreak",
    pattern=_p(
        r"(?:rot[\s-]?13|vigen[eè]re|caesar\s+cipher|base64|rot\s*\d+)\b"
        r"[\s\S]{0,150}"
        r"(?:decode|decrypt|decipher|translate)\b"
        r"[\s\S]{0,150}"
        r"(?:then\s+(?:execute|follow|apply|do|run|perform|act\s+on)|"
        r"and\s+(?:execute|follow|act\s+on)\s+(?:the\s+)?(?:instruction|result|output))"
    ),
    base_score=60,
    description=(
        "RoguePrompt attack: the input encodes a jailbreak payload using a named cipher "
        "(ROT-13, Vigenère, Caesar) and embeds decoding instructions that ask the model to "
        "decode and then execute the result. This dual-layer approach achieved 93.93% filter "
        "bypass and 70.18% execution success across 313 hard-rejected prompts "
        "(arxiv:2511.18790, Nov 2025)."
    ),
    owasp_ref="OWASP LLM01: Prompt Injection / LLM07: System Prompt Leakage",
    remediation_hint=(
        "Reject inputs that combine a named encoding/cipher reference with a directive to "
        "decode and execute the result. The decode-then-execute pattern is the defining "
        "signal of this attack; standalone cryptography questions are not covered."
    ),
)
```

## Why Held Back

**False-positive risk:** The proposed pattern requires a named cipher + decode + execute-then
structure. However:
- Legitimate cryptography tutorials and exercises commonly ask "decode this ROT-13 string"
- The execute-then condition narrows it, but phrasing like "then follow the instructions
  in the decoded text" is still edge-case in CTF/homework contexts
- LOC budget was not the constraint; FP tuning is.

## Suggested Next Step

In the next `jailbreak-extraction` or `evasion-obfuscation` cycle:
1. Collect 5–10 real RoguePrompt examples from arxiv:2511.18790 appendix
2. Verify false-positive rate against legitimate cryptography prompts in a benign corpus
3. If FP rate is acceptable (<1%), implement with the pattern above
4. Optionally combine with an output filter that detects ROT-13/Vigenère-encoded content in
   model responses (signs the model decoded and is responding to the hidden payload)
