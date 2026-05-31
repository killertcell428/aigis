# Pending: StegoAttack Sentence-Initial Acrostic Detection

## Title
Detect sentence-initial steganographic jailbreaks (StegoAttack)

## Motivation
StegoAttack (arxiv:2505.16765, 2025) hides harmful queries by encoding them as the first
letter (or word) of each sentence in a benign-looking paragraph. The cover text reads as
natural prose on an unrelated topic. Average ASR of 95.5% across safety-aligned LLMs;
≥69% success even with active Llama Guard deployed. Because the surface text is benign,
perplexity-based filters and semantic content classifiers cannot flag it — only the
decoded acrostic reveals the true intent.

## Research finding
StegoAttack: "When Safety Detectors Aren't Enough" (arxiv:2505.16765, May 2025)
https://arxiv.org/abs/2505.16765

## Proposed change
Add a function in `aigis/filters/input_filter.py` (or a new `aigis/decoders.py` utility)
that:
1. Segments input into sentences.
2. Extracts the first letter of each sentence to reconstruct the acrostic.
3. Scores the acrostic against `PROMPT_INJECTION_PATTERNS` and `JAILBREAK_ROLEPLAY_PATTERNS`.
4. If the acrostic matches a known-dangerous pattern, flag as `jb_stegoattack` with score 70.

## Why held back
Implementation requires:
- Sentence segmentation (ideally spaCy or NLTK, adding a runtime dependency), or
- A naive period/exclamation/question-mark splitter (zero dependencies but low recall).
- The naive splitter is feasible but will miss sentences ending with colons, ellipses, etc.
- False-positive risk: legitimate text where initials happen to spell a common phrase.

## Constraint that blocked it
The zero-dependency constraint complicates sentence segmentation. A naive implementation
(split on `.!?\n`) is viable but has material false-positive risk without POS tagging.

## Suggested next step
Implement in a future evasion-obfuscation cycle using the naive sentence splitter with
a higher score threshold (85+) and requiring the decoded acrostic to match a high-confidence
pattern (score 70+) before flagging. This reduces false positives at the cost of some recall.
