# Pending: Multi-Stream Perturbation Heuristic for Thinking-Mode LLMs

## Title
Detection heuristic for multi-stream concurrent task interleaving targeting reasoning-mode LLMs

## Motivation
The Multi-Stream Perturbation Attack (arxiv:2603.10091, Mar 2026) disrupts safety alignment in
thinking-mode LLMs (Qwen3, DeepSeek-R1, Gemini 2.5 Flash) by interleaving three or more
seemingly independent task streams within a single prompt. The concurrent cognitive load collapses
the model's chain-of-thought reasoning and causes safety guardrails to fail. Thinking collapse
rates up to 17% and response repetition up to 60% were measured.

## Research finding that led to this idea
- arxiv:2603.10091 (Mar 2026): Three perturbation strategies — multi-stream interleaving,
  inversion perturbation (character reversal), and shape transformation — break thinking-mode
  safety alignment on Qwen3-Max, DeepSeek, and Gemini 2.5 Flash.

## Proposed change
Add a heuristic in the input filter that counts the number of structurally distinct task streams
in a single prompt (e.g., by detecting 3+ separate numbered lists, instruction blocks, or
`Task N:` / `Step N:` headings interleaved with each other in a pattern suggesting concurrent
rather than sequential instructions). Flag inputs with 3+ concurrent task streams combined with
sensitive content keywords as high-risk.

## Why it was held back
- Defining "concurrent task stream" at the text level is inherently heuristic and high
  false-positive risk (legitimate complex instructions often have multiple numbered steps).
- The attack targets model reasoning behavior, not text-level patterns — there is no reliable
  textual fingerprint distinguishing a multi-stream attack from a legitimate multi-part question.
- Building a reliable heuristic with <5% FPR requires empirical tuning against a labeled dataset
  we do not currently have.

## Which constraint blocked it
- "Keep total non-test diff ≤ 100 LOC" and "Do not add features that depend on calling an LLM
  at runtime": a reliable structural parser for multi-stream patterns would exceed 100 LOC and
  the heuristic alone would have unacceptably high false positives without LLM-assisted
  classification.

## Suggested next step for human reviewer
Collect a small labeled dataset of multi-stream attack vs. legitimate complex-prompt examples,
then evaluate whether a simple feature (e.g., regex counting of "Task N:" patterns combined with
line-reversal indicators) achieves acceptable precision. If precision > 90% at a sample size of
200 examples, implement as a low-score (15–20) flag rather than a block.
