# Pending: Variation Selector Concentration Heuristic

**Date:** 2026-05-11
**Research finding:** auto-improvement/research/2026-05-11T12-15_7-evasion-obfuscation.md (finding 2)
**Constraint blocking:** High false-positive rate with emoji text; requires per-codepoint context analysis.

---

## Title

Detect unusual concentrations of Unicode variation selectors (U+FE00–U+FE0F) as adversarial invisible suffixes.

## Motivation

arxiv:2510.05025 (NUS, Oct 2025) demonstrated "imperceptible jailbreaks" using adversarially optimized sequences of variation selectors appended to attack prompts. The variation selectors are invisible to humans and stripped by most guardrail classifiers (which tokenize them as noise), but the underlying LLM tokenizer processes them as part of the input, allowing an optimized bit sequence hidden in them to steer harmful outputs. High attack success rate demonstrated against GPT-4, Claude, Llama, and Gemini.

Repello AI found a related "emoji smuggling" variant achieving 100% ASR against Azure Prompt Shield and Protect AI v2, also using variation selectors attached to emoji characters.

## Proposed Change

Add a detection heuristic in `aigis/filters/patterns.py` or a custom pre-filter:

```python
# Count variation selectors (U+FE00–U+FE0F) relative to text length.
# Normal text has 0; adversarial suffixes may have dozens.
_VS_RE = re.compile(r"[︀-️]")

def check_variation_selector_density(text: str) -> bool:
    """Flag if variation selectors appear more than once per 10 chars on average."""
    if len(text) < 20:
        return False
    vs_count = len(_VS_RE.findall(text))
    return vs_count > 0 and (len(text) / max(vs_count, 1)) < 10
```

Or as a DetectionPattern with a regex like `[︀-️]{3,}` (3+ consecutive variation selectors with no base character between them).

## Why Held Back

1. **False positive risk:** Emoji legitimately use variation selectors. VS-15 (U+FE0E) and VS-16 (U+FE0F) select text vs. emoji presentation for many codepoints (e.g., ☎️ = ☎ + U+FE0F). A text with several emoji may have many VS-16 instances.
2. **Context-dependency:** Distinguishing legitimate emoji VS usage from adversarial VS stuffing requires knowing whether each VS is attached to a base character that has a defined variation. This needs a Unicode variation sequences table.
3. **Threshold tuning:** The adversarial case involves dense VS sequences (10–50 selectors in a suffix). The legitimate case is sparse (1 per emoji). A count-based threshold is feasible but needs benchmarking.

## Constraint Blocking

Not a hard constraint violation, but FPR concerns require careful tuning before shipping. The variation selector space is legitimate Unicode and cannot be blanket-blocked.

## Suggested Next Step

1. Collect a representative corpus of emoji-rich text (e.g., social media excerpts) and measure baseline VS density.
2. Test against the adversarial samples from arxiv:2510.05025 (code at https://github.com/sail-sg/imperceptible-jailbreaks).
3. Implement as a DetectionPattern with a threshold-based regex, e.g., `[︀-️]{4,}` (4+ consecutive VS with no base char — always adversarial), plus a density-based pre-filter for cases where VS are spread out.
