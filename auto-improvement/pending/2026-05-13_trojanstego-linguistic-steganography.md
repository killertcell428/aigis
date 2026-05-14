# Pending: TrojanStego / Linguistic Steganography Detection

## Title
Detection or documentation for fine-tuned LLM output steganography (TrojanStego)

## Motivation
arxiv:2505.20118 (May 2025) describes TrojanStego: adversaries fine-tune an LLM to embed sensitive
context information into natural-looking outputs via linguistic steganography — whitespace substitution,
punctuation encoding, subtle token-choice patterns. The resulting outputs look completely normal to
human readers but carry a hidden bit-stream. Demonstrated 87% single-pass accuracy, >97% with majority
voting. arxiv:2410.03768 additionally shows that steganographic collusion between LLM agents can arise
unintentionally from misspecified reward incentives during training.

## Research finding that led to this idea
Research file: `auto-improvement/research/2026-05-13T06-13_2-data-exfiltration.md`
- Findings: arxiv:2505.20118, arxiv:2410.03768

## Proposed change
1. Add a hardening guide under `docs/` explaining linguistic steganography as a model-level supply
   chain risk distinct from prompt-injection-based exfiltration.
2. Document the detection approach from arxiv:2603.28655 (steganographic canaries): operators can
   embed zero-width Unicode canary tokens in system prompts and monitor outbound text for their
   presence; if a canary appears in agent output (especially in encoded form), it suggests a
   steganographic channel.
3. Optionally, add an aigis output-filter heuristic that flags outputs containing an anomalously
   high density of Unicode variation selectors or zero-width joiners, which are common in some
   steganographic encoding schemes.

## Why it was held back
The core exfiltration channel (token choice distribution, whitespace substitution) is statistical
and syntactically indistinguishable from normal text. A regex cannot detect it. The canary-token
approach requires runtime state injection, not a passive pattern matcher.

## Constraint that blocked it
- Rule-based architecture: statistical steganography requires output distribution analysis (entropy,
  perplexity, or token-rank monitoring), which is beyond the scope of a `DetectionPattern` regex.
- Adding a zero-width character density heuristic could be done (regex for `​`, `‌`,
  `‍`, `﻿` density) but would need empirical tuning to avoid false positives in legitimate
  multilingual outputs.

## Suggested next step for human reviewer
1. Write a hardening guide doc for the statistical steganography risk and canary-token mitigation.
2. Consider adding a lightweight zero-width character density check to OUTPUT_PATTERNS as a separate
   low-score pattern, tuned with empirical multilingual test data.
3. Reference: arxiv:2505.20118 (TrojanStego, May 2025), arxiv:2603.28655 (steganographic canaries,
   Mar 2026), arxiv:2410.03768 (steganographic collusion, Oct 2024).
