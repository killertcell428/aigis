# Pending: ASCII Art Instruction Detection

## Title
`enc_ascii_art_instruction` — Detect explicit instructions to interpret ASCII art as attack keywords

## Motivation
ArtPrompt (ACL 2024, arxiv:2402.11753) demonstrates that representing sensitive keywords as
ASCII art (e.g., a large grid of `*` and space characters spelling "BOMB") bypasses safety
classifiers because classifiers see random symbols while LLMs recognize the visual pattern.
Five SOTA LLMs (GPT-3.5, GPT-4, Gemini, Claude, Llama-2) were all vulnerable, with
ArtPrompt achieving mean harmfulness 3.6/5 vs. 2.67 for PAIR — the next best method.

The attack requires an explicit instruction framing: "interpret this ASCII art," "the following
ASCII art represents the word X," "recognize what this ASCII art says."

## Research finding
ArtPrompt: ASCII Art-based Jailbreak Attacks against Aligned LLMs
arxiv:2402.11753 (ACL 2024)
https://arxiv.org/abs/2402.11753

## Proposed change
Add `enc_ascii_art_instruction` to `ENCODING_BYPASS_PATTERNS` in `aigis/filters/patterns.py`.

Proposed pattern (instruction-only detection, not art recognition):
```python
r"(?:interpret|recognize|read|understand|decode|tell\s+me\s+what)\s+(?:this\s+)?(?:ascii|text)\s+art"
r"|(?:the\s+following\s+(?:ascii\s+art|text\s+art|characters?)\s+(?:represent|spell|shows?|means?|says?))"
r"|(?:ascii\s+art\s+(?:for|of|representing|that\s+(?:says|means|spells)))"
```

Score: 35 (explicit instruction is a strong but not definitive signal — the art may be benign).

## Why held back
**False-positive risk:** Agent pipelines legitimately use ASCII art for:
- Diagram generation (text-based flowcharts, box-drawing)
- Chart/table rendering in terminal environments
- Creative writing assistants that generate ASCII art on request
- Documentation of CLI tools that show ASCII art banners

An instruction like "interpret this ASCII art banner for the project logo" would trigger.

## Constraint that blocked it
Moderate FPR risk in AI agent pipelines that produce or discuss ASCII art as a legitimate
feature. Without context about what keyword the art represents, cannot distinguish benign
from malicious usage.

## Suggested next step
Combine the instruction pattern with a co-occurrence check: if the instruction appears in
the same sentence/paragraph as known dangerous keywords (bomb, weapon, hack, etc.) in any
form, raise the score. Otherwise keep at baseline 20. This two-component approach would
significantly reduce FPR.
