# Pending: jb_code_decrypt_stub — CodeChameleon def decrypt() Pattern

## Title
`jb_code_decrypt_stub` — Detect CodeChameleon code-completion decryption frames

## Motivation
CodeChameleon (arxiv:2402.16717, 2024) embeds a harmful query inside a Python `ProblemSolver`
class. A `def decrypt()` function decodes the hidden payload and a `solve()` method calls it.
The LLM is asked to "complete" the class. Measured 86.6% ASR on GPT-4-1106. The `def decrypt(`
or `class ProblemSolver` stub is a near-unique signal rarely found in legitimate prompts.

## Research finding
- Source: https://arxiv.org/abs/2402.16717
- CodeChameleon: Personalized Encryption Framework for Jailbreaking Large Language Models
- ASR: 86.6% on GPT-4-1106; evaluated across 7 LLMs

## Proposed change
Add `jb_code_decrypt_stub` to `JAILBREAK_ROLEPLAY_PATTERNS`:

```python
pattern=_p(
    r"(?:"
    r"def\s+decrypt\s*\(|"
    r"def\s+decode\s*\(.{0,100}encrypted|"
    r"class\s+ProblemSolver\b|"
    r"\.solve\s*\(\s*[\"'][^\"']{15,}[\"']\s*\)"
    r")"
),
```

## Why it was held back
Cycle LOC budget exhausted.

## Which constraint blocked it
> "Keep total non-test diff ≤ 100 LOC."

## Suggested next step
Implement in a future jailbreak-extraction or evasion-obfuscation cycle. Ensure false-positive
test covers legitimate uses of `def decrypt()` (e.g., implementing AES decryption in a tutorial).
