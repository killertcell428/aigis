# Pending: PUZZLED Word-Puzzle Decode Instruction Detection

## Title
Add `enc_word_puzzle_instruction` detection pattern for anagram/word-search-based jailbreaks

## Motivation
PUZZLED (arxiv:2508.01306, August 2025) jailbreaks LLMs by masking harmful keywords inside
word-puzzle formats (anagram challenges, word search grids, crossword clues) and instructing the
LLM to solve the puzzle to reconstruct and then execute the harmful instruction. Achieves 88.8%
average ASR across five state-of-the-art LLMs: 96.5% on GPT-4.1, 92.3% on Claude 3.7 Sonnet,
and high rates on Llama, Gemini, and Mistral models.

The "decode instruction" is detectable in plaintext: phrases like "solve this anagram:",
"find the hidden word:", "complete this word search:", or "unscramble these letters:"
followed by a scrambled payload.

## Research Finding
`auto-improvement/research/2026-05-16T03-08_7-evasion-obfuscation.md` — Finding #2.

## Proposed Change
Add a new `DetectionPattern` to `ENCODING_BYPASS_PATTERNS`:

```python
DetectionPattern(
    id="enc_word_puzzle_instruction",
    name="Word-Puzzle Decode Instruction (Anagram / Word Search Jailbreak)",
    category="encoding_bypass",
    pattern=_p(
        r"(?i)(?:"
        r"(?:solve|complete|decode|read|find)\s+(?:this|the|an?)?\s+(?:word\s*(?:search|puzzle|grid|finder)|anagram|crossword\s*(?:clue)?)"
        r"|(?:un)?scramble\s+(?:these\s+)?(?:letters|words)"
        r"|anagram\s*[:\-]\s*\w"
        r")"
    ),
    base_score=35,
    ...
)
```

## Why Deferred
Moderate false-positive rate in legitimate educational and puzzle contexts:
- "solve this anagram: ..." appears in word games and language learning apps
- "complete the word search" is legitimate educational content
- "unscramble these letters" is a standard vocabulary exercise prompt

A score of 35 would make this an amplifying signal rather than a blocker, but needs empirical
tuning against a corpus of legitimate puzzle/educational prompts before deployment.

## Constraint
Better handled after collecting false-positive test cases from real-world educational
and puzzle contexts to calibrate the threshold and keyword list.

## Suggested Next Step
1. Collect 20–30 examples of legitimate "anagram/word-search" prompts.
2. Tune the pattern to require more specific context (e.g., anagram + instruction word + known
   attack keyword in proximity) to reduce FPR.
3. Consider adding as a low-score pattern (20–25) that only contributes to a risk score when
   other signals are also present.
4. Reference: arxiv:2508.01306 (PUZZLED, August 2025).
