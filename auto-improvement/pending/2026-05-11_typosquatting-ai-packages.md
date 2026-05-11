# Pending: Typosquatting Heuristic for AI/ML Package Names

**Cycle:** 5 (second pass) · **Domain:** supply-chain-llm · **UTC:** 2026-05-11T00-00

---

## Title

Levenshtein-distance typosquatting detector for AI/ML Python packages

## Motivation

RH-ISAC (2025-2026) documented automated campaigns deploying 300+ typosquatted
packages mimicking core AI/ML libraries (`transformers`, `langchain`, `llama-index`,
`pytorch`, `tensorflow`, `sentence-transformers`, etc.). Payloads include zgRAT
malware deployed via pip install hooks. Pip's case-insensitivity and
hyphen/underscore equivalence (PEP 503 normalization) are exploited to create
nearly indistinguishable package names.

Source: https://rhisac.org/threat-intelligence/typosquatting-campaign-targets-python-developers-with-hundreds-of-malicious-libraries/

## Proposed change

Add a `sc_ai_pkg_typosquatting` detector that:
1. Maintains a short whitelist of ~20 canonical AI/ML package names.
2. In the `pip install <pkg>` context, extracts the package name.
3. Computes Levenshtein distance against each canonical name.
4. Flags if distance ≤ 2 AND the name is NOT in the exact-match whitelist.

## Why held back

**Constraint violated: maintenance burden for the rule-based philosophy.**
The detector requires a maintained whitelist of canonical names. Any omission
creates false negatives; any wrong entry creates false positives. The current
aigis approach uses exact regex patterns rather than heuristic distance scoring.
Adding a distance function also nudges the codebase toward runtime computation
rather than pure regex matching.

## Suggested next step

- Compile a canonical package list (`aigis/supply_chain/known_safe_packages.py`).
- Implement `levenshtein_distance()` as a pure-Python utility (no runtime dep).
- Gate the detector behind an opt-in flag (`enable_typosquatting_heuristic=False`).
- Add a test fixture with known typosquatted names from the RH-ISAC incident list.
- Once the list is stable across one release cycle, make the flag default-True.
