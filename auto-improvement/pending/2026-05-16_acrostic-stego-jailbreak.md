# Pending: Acrostic Steganographic Jailbreak (StegoAttack)

**Date:** 2026-05-16
**Research finding:** auto-improvement/research/2026-05-16T00-00_7-evasion-obfuscation.md (finding 3)
**Constraint blocking:** Not detectable by rule-based regex methods; requires LLM-based semantic analysis.

---

## Title

Detect acrostic steganographic jailbreaks where a harmful query is hidden as the first letter of each sentence in an otherwise benign-looking paragraph.

## Motivation

StegoAttack (arxiv:2505.16765, Nankai University, May 2025) achieves 95.50% average attack success rate across four safety-aligned LLMs including GPT-4 variants and Gemini, outperforming all eight evaluated jailbreak baselines.

The attack mechanism: an attacker LLM generates a benign, fluent paragraph where the first letter of each sentence spells out the harmful query. Example: a paragraph about cooking where the first letters of sentences spell "HOW TO MAKE METH". The cover text passes semantic classifiers (no surface red flags). The receiving LLM's instruction-following tendency causes it to decode and answer the hidden question.

The attack simultaneously achieves:
- **Semantic stealth:** the cover paragraph contains no explicit harmful content
- **Linguistic stealth:** the cover text is grammatically correct and contextually coherent
- **High ASR:** 95.5% average across four safety-aligned models; drops by less than 27% under external safety detectors

## Proposed Change (Hypothetical)

There is no clean rule-based implementation. A potential future approach:

1. **Structural heuristic:** Extract first characters of each sentence/line. Re-scan the acrostic as a standalone string. This catches simple cases but not mixed-case or word-level acrostics.
2. **LLM-based detection:** Pass the text to a safety classifier and ask it to identify any hidden messages. This requires an LLM call at runtime — violates the zero-runtime-dependency constraint.
3. **Statistical anomaly:** Flag paragraphs where the first characters of sentences spell unusually many consonant-consonant transitions (which are rare in English sentence-starting words). Very high FPR.

None of these approaches is implementable as a simple DetectionPattern regex.

## Why Held Back

1. **Hard constraint violation:** Any effective detection requires either calling an LLM (runtime dependency) or complex NLP analysis (not rule-based).
2. **FPR risk:** Rule-based approaches would have very high false-positive rates on legitimate content where sentence-starting letters coincidentally spell short words.
3. **Philosophy:** aigis is explicitly a zero-runtime-dependency, rule-based firewall. Acrostic detection is out of scope for the current architecture.

## Suggested Next Step

1. If aigis adds an optional LLM-backed scanning mode in the future, acrostic detection is a natural candidate for that mode.
2. For the current architecture, the best defense is documentation: inform aigis users that multi-sentence prompts with unusual structure should trigger manual review in high-risk contexts.
3. Consider adding a documentation note to `docs/` about this attack class and its limitations for rule-based detection.
