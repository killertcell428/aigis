# Pending: SequentialBreak Attention-Dilution Detection

## Title
Detect SequentialBreak-style harmful prompts hidden in a chain of benign prompts

## Motivation
SequentialBreak (arxiv:2411.06426, Nov 2024, updated May 2025) embeds a single harmful
prompt at an optimal position (position 4 of 6 in tested configurations) within a chain
of benign prompts in one query. The model's attention distributes across all prompts and
the harmful request is "laundered" by surrounding benign context. Surpasses PAIR,
DeepInception, and ReneLLM baselines across GPT-3.5, GPT-4, Llama2, Llama3, Gemma2, Vicuna.
The attack exploits transformers' position-weighted attention — early and late positions
receive more focused attention, so the middle position is the optimal hiding spot.

## Research finding
SequentialBreak: "Large Language Models are Easily Fooled by Sequential Prompts" (arxiv:2411.06426)
https://arxiv.org/abs/2411.06426

## Proposed change
Add a `jb_sequential_chain_injection` pattern to `JAILBREAK_ROLEPLAY_PATTERNS`:
1. Detect inputs containing 4+ numbered or bulleted distinct questions.
2. Within those questions, check if any contains a known-dangerous keyword or high-risk phrase.
3. Score only if the structural chain is present AND a dangerous-keyword match occurs.

Example regex sketch:
```python
r"(?:(?:\d+\.\s+|\*\s+|-\s+)[^\n]+\n?){3,}[\s\S]{0,500}(?:harmful_keyword)"
```

## Why held back
Position-aware analysis requires knowing which question is at "position 4 of 6" — this
depends on counting and ordering questions, which is doable with regex groups but brittle.
More importantly, numbered lists with one dangerous item embedded is a high false-positive
scenario for legitimate technical Q&A. Without semantic understanding of the surrounding
items, distinguishing "a harmful prompt laundered by benign questions" from "a technical FAQ
that happens to include one edge-case question" is unreliable with pure regex.

## Constraint that blocked it
False-positive risk in legitimate multi-question technical inputs. Position-dependent
analysis beyond simple pattern matching.

## Suggested next step
Pick up in a multi-agent cycle with a two-component approach:
1. Structural check: numbered list with 4+ items.
2. Dangerous-keyword check with high-confidence keyword (score 70+ in existing patterns).
3. Combine both with a scoring bonus rather than a standalone rule.
