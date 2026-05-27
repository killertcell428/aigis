# Pending: Doublespeak / Codeword Substitution Setup (`jb_codeword_substitution`)

**Date:** 2026-05-27
**Research basis:** `auto-improvement/research/2026-05-27T03-12_3-jailbreak-extraction.md`

## Title
In-context codeword substitution setup (Doublespeak)

## Motivation
Doublespeak / In-Context Representation Hijacking (arxiv:2512.03771, 2025, ICLR submission)
provides in-context examples where a benign word (e.g., "carrot") is consistently substituted
for a harmful keyword (e.g., "bomb"). After enough consistent examples, the model's internal
representation of the benign word converges toward the harmful concept. The final query —
"How do I build a carrot?" — is then processed as if it asked about the harmful object.
74% ASR on Llama-3.3-70B-Instruct; optimization-free; no gradient access required;
transfers across model families.

The substitution-setup phase is detectable: it produces distinctive phrases like
"in this conversation, [word] means [word]", "whenever I say X, I mean Y", or
"X is a codeword for Y".

## Research Finding
Source: https://arxiv.org/abs/2512.03771

## Proposed Change
Add `jb_codeword_substitution` to `JAILBREAK_ROLEPLAY_PATTERNS`:

```python
DetectionPattern(
    id="jb_codeword_substitution",
    name="Doublespeak / In-Context Codeword Substitution Setup",
    category="jailbreak",
    pattern=_p(
        r"(?:in\s+this\s+(?:conversation|context|chat|session)|"
        r"for\s+this\s+(?:conversation|exercise|context|purpose)|"
        r"from\s+now\s+on|let['’]?s\s+say|whenever\s+I\s+say)\s*"
        r"[\s\S]{0,60}?"
        r"(?:['\"]?\w+['\"]?\s+)?(?:means?|refers?\s+to|stands?\s+for|is\s+a\s+codeword\s+for|"
        r"represents?|is\s+used\s+(?:to\s+mean|for|as\s+a\s+stand-?in)|"
        r"should\s+be\s+(?:interpreted|read|understood)\s+as)\s+"
        r"['\"]?\w"
    ),
    base_score=55,
    description=(
        "Doublespeak codeword substitution setup: the prompt establishes an in-context "
        "semantic mapping where a benign word stands in for a harmful concept ('carrot "
        "means bomb'). arxiv:2512.03771 showed that consistent substitution examples "
        "shift the model's internal representation of the benign word toward the harmful "
        "concept, achieving 74% ASR on Llama-3.3-70B without optimization or gradient "
        "access. The setup phrase is detectable before the final malicious query is sent."
    ),
    owasp_ref="OWASP LLM01: Prompt Injection",
    remediation_hint=(
        "Prompts that establish word-substitution mappings ('X means Y', 'whenever I say "
        "X treat it as Y') are a semantic-hijacking setup. Treat any in-context definition "
        "that renames one concept as another as a potential codeword attack and apply "
        "elevated scrutiny to subsequent queries in the session."
    ),
),
```

## Why Held Back
LOC budget (100 LOC non-test) was used by `jb_payload_splitting` and `jb_translation_extraction`
in this cycle.

## Constraint
LOC budget exhausted this cycle.

## Suggested Next Step
Implement in the next `jailbreak-extraction` cycle. False positive risk: legitimate "for this
exercise, let's say X means Y" is common in language learning and games; scoring at 55 means
it needs co-occurring signals to reach HIGH.
