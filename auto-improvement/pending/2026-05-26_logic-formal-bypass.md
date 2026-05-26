# Pending: Logic Jailbreak (LogiBreak) Unicode Operator Detection

## Title
`jb_logic_formal_bypass` — Detect jailbreak prompts that encode harmful requests in formal
logical notation to evade natural-language safety classifiers.

## Motivation
LogiBreak (arxiv:2505.13527, Peng et al., May 2025) converts harmful natural-language prompts
into formal logical expressions using Unicode operators (∀, ∃, ⟹, ∴, ¬, ∧, ∨) or their
spelled-out equivalents ("for all", "there exists", "implies", "therefore"). Safety fine-tuning
datasets do not include formal-logic-notation inputs, so models' safety guardrails are less
reliable when the harmful intent is expressed in predicate form.

## Research finding that led to this idea
`auto-improvement/research/2026-05-26T00-07_3-jailbreak-extraction.md` — LogiBreak finding.

## Proposed change
Add a `jb_logic_formal_bypass` pattern to `JAILBREAK_ROLEPLAY_PATTERNS` in
`aigis/filters/patterns.py`:

```python
DetectionPattern(
    id="jb_logic_formal_bypass",
    name="Formal Logic Notation Jailbreak (LogiBreak)",
    category="jailbreak",
    pattern=_p(
        r"(?:∀|∃|∴|⟹|⊢|⊨)"
        r".{0,400}?"
        r"(?:output|must\s+(?:answer|respond|provide|give|generate)|"
        r"without\s+(?:restrict|censor|filter|refus)|"
        r"ignor(?:ing|e)\s+(?:safety|restriction|filter|policy|guardrail))"
    ),
    base_score=50,
    ...
)
```

## Why it was held back
False-positive risk: Unicode logical operators (∀, ∃, ⟹) appear legitimately in mathematical
proofs, computer science papers, formal verification discussions, and logic coursework. Without
a way to distinguish a genuine proof from a logic-form jailbreak, the rule would produce too
many false positives for engineering and academic use cases. A higher-confidence version would
require combining the Unicode signal with a harmful-topic keyword, which would require
maintaining a harmful-keyword list (adding complexity).

## Which constraint blocked it
Practical quality constraint: false-positive rate too high for a rule with base_score=50+ in
contexts where formal logic is legitimate.

## Suggested next step for human reviewer
1. Gather real LogiBreak attack examples from the arxiv:2505.13527 paper's evaluation dataset.
2. Measure false-positive rate against a corpus of legitimate mathematical discussions.
3. Consider adding as an optional/off-by-default rule if FP rate exceeds 1 in 1000 for
   engineering contexts.
4. Alternatively, implement as an output-filter rule (post-response scanning) where false
   positive risk is lower.
