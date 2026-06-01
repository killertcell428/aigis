# Pending: Low-Resource Language Translation Bypass Detection

## Title
Language-identification filter for low-resource language jailbreak bypass

## Motivation
Models trained primarily on English have weaker safety alignment in low-resource languages
(Zulu, Hausa, Amharic, Yoruba, Swahili, etc.). Attackers exploit this disparity by translating
harmful requests into a low-resource language before submission. arxiv:2605.18239 (May 2026)
documented 60–89% ASR with human evaluation across 15 low-resource languages on multiple
commercial LLMs including GPT-4o and Claude.

## Research finding that led here
- Source: https://arxiv.org/html/2605.18239v1

## Proposed change
Add an optional language-identification step in `Guard.scan_input()`:
- Use `langdetect` (pure Python, no network dependency) to identify the language of each input
- If the detected language is in a configurable low-resource denylist, increase the base risk
  score by a configurable amount (default: +20)
- Expose as `Guard(block_low_resource_languages=True, low_resource_language_score_bump=20)`
- Default: disabled (backward compatible)
- The denylist should be configurable and default to the 10 languages with the lowest
  representation in LAION-5B / Common Crawl training corpora

## Why it was held back
`langdetect` is a new runtime dependency (not currently in pyproject.toml). Adding a required
runtime dependency violates the zero-runtime-dependency constraint. Even as an optional extra
(e.g., `pip install aigis[multilingual]`), it requires design decisions about import-time
behavior when the extra is absent.

## Constraint that blocked it
"Do NOT add features that depend on calling an LLM at runtime, and do NOT add new required
runtime dependencies." Even as optional, the dependency design needs careful review.

## Suggested next step for the human reviewer
Evaluate whether `langdetect` (or `lingua-language-detector`, a lighter alternative) is
acceptable as an optional extra dependency with a graceful no-op fallback when absent.
If approved, implement as `aigis[multilingual]` optional extra with documented install path.
