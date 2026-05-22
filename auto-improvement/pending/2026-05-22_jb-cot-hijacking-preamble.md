# Pending: Chain-of-Thought Hijacking via Benign Preamble (`jb_cot_hijacking_preamble`)

**Date:** 2026-05-22
**Cycle:** 3 (jailbreak-extraction fourth pass)
**Research source:** Research file `2026-05-22T03-02_3-jailbreak-extraction.md`

---

## Title

Detection for CoT hijacking via long benign preamble before a harmful request

## Motivation

Chain-of-Thought Hijacking (arXiv:2510.26418, Oct 2025) prepends a harmful request with an
extended sequence of genuinely benign reasoning content — long math puzzles, word games, or logic
exercises — that consumes the model's attention and dilutes the safety signal in mid-layer
activations. When the harmful request arrives at the end, refusal collapses. A related technique,
H-CoT (arXiv:2502.12893, Feb 2026), wraps malicious requests inside the model's own displayed
chain-of-thought reasoning.

Published attack success rates:
- 99% on Gemini 2.5 Pro
- 100% on Grok 3 Mini  
- 94% on Claude 4 Sonnet
- 94% on ChatGPT o4-mini

The "Seduction" pipeline structure:
1. Long benign preamble (word puzzles, math problems, creative exercises)
2. Transition phrase: "Now that we've warmed up…", "Great, for the next task…"
3. Harmful request attached at the end

## Proposed Change

A heuristic for single-turn detection: flag prompts where:
- Total length > 800 chars
- A harmful keyword appears in the final 15% of the prompt
- The first 60% contains structured benign content (Q&A format, numbered problems, definitions)

This is difficult to express as a single regex but could be a composite heuristic function
in `aigis/filters/fast_screen.py` or as a post-scoring adjustment in the scanner.

## Why Held Back

**Architecture constraint:** The detection logic requires a length-proportional match — checking
where in the prompt the harmful keyword appears relative to total length. This is not expressible
as a `DetectionPattern` regex alone. It would require changes to the `Scanner` or `fast_screen`
pipeline, which may affect public API behavior.

**LOC budget:** A robust implementation would need 50-80 LOC in the scanner, plus tests,
exceeding single-cycle non-test LOC budget when combined with other changes.

## Suggested Next Step

Implement as an optional `fast_screen` heuristic: add a `length_weighted_score_boost()` function
that increases the effective score of a late-appearing harmful keyword proportionally to the
benign preamble length. Keep it opt-in (default behavior unchanged).

## Sources

- arXiv:2510.26418 — Chain-of-Thought Hijacking (Oct 2025)
- arXiv:2502.12893 — H-CoT: Hijacking Chain-of-Thought Safety Reasoning (Feb 2026)
