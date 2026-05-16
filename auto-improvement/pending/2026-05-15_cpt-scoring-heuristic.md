# Pending: Characters-Per-Token (CPT) Scoring Heuristic

**Title:** CPT (Characters-Per-Token) obfuscation scoring layer

**Motivation:**
arxiv:2510.26847 (Oct 2025) proposes "Broken-Token" CPT filtering as a lightweight defense:
normal English text averages ~4.5 characters per (whitespace-delimited) token. Obfuscated text
— diacritics floods, combining character sequences, BIDI insertions, fullwidth Latin — drops
to 1–2 chars/token. A threshold of 3.0 chars/token catches >85% of obfuscated inputs at <1%
false positive rate without requiring access to the actual LLM tokenizer.

**Which research finding led to this idea:**
- arxiv:2510.26847 — "Broken-Token: Filtering Obfuscated Prompts by Counting Characters-Per-Token"

**Proposed change:**
Add a scoring function (not a DetectionPattern) that:
1. Splits input on whitespace to get an approximate token count.
2. Divides character count by token count to get CPT ratio.
3. If CPT < 3.0 and input is longer than 20 tokens (to exclude short strings), adds a risk
   penalty (e.g., +25 score) flagged as "suspicious_cpt_ratio".

This would serve as a generic obfuscation detector complementing the specific pattern rules
(diacritics, zalgo, fullwidth, etc.), catching novel obfuscation techniques not yet in the
pattern library.

**Why it was held back:**
The `DetectionPattern` architecture is a compiled regex + metadata. CPT scoring is a
numeric calculation, not a pattern match. Adding it requires either:
(a) A new scorer type (e.g., `ScoringHeuristic`) in the filter architecture, or
(b) A hack using a regex callback, which is complex and fragile.

Adding a new scorer type is a non-trivial architectural change that touches `guard.py`,
`scanner.py`, and the public API. This exceeds the 100-LOC limit for a single cycle and
represents a directional change in the architecture.

**Which constraint blocked it:**
"Total non-test diff ≤ 100 LOC" and "no breaking public API change without explicit
opt-in." A new `ScoringHeuristic` type would require changes to the `Guard`, `Scanner`,
and possibly `AuditLog` classes.

**Suggested next step for human reviewer:**
Design a `ScoringHeuristic` abstract base class alongside `DetectionPattern`. It would
expose a `score(text: str) -> int` method and be collected alongside patterns in `Guard`.
The CPT heuristic would be the first concrete implementation. This architecture would also
be the correct home for the variation selector density check (see separate pending note).
