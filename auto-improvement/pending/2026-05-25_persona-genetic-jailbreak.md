# Pending: Persona-Enhanced Genetic Jailbreak Detection

## Title
New or extended jailbreak rule for genetic-algorithm-evolved persona prompts

## Motivation
Zhang et al. (arxiv:2507.22171, HKUST/Tencent, Jul 2025) demonstrate that automatically
evolving persona prompt descriptions via a genetic algorithm reduces LLM refusal rates by
50–70% across tested models. When combined with existing jailbreak methods, these evolved
personas increase attack success rates by a further 10–20%. The key mechanism is that
the evolved persona description creates a character framing that exploits alignment
blind spots — the model becomes "more inclined to respond" rather than refusing.
The research also shows that evolved persona prompts defeat character-focused safety
training more reliably than hand-crafted personas.

## Research finding that led to this idea
Research file: `auto-improvement/research/2026-05-25T09-02_3-jailbreak-extraction.md`
- Finding: Persona-Enhanced Genetic Jailbreak (arxiv:2507.22171)

## Proposed change
1. If representative evolved-persona examples from the paper are publicly available,
   extract the distinguishing phrase patterns (e.g., compound character descriptors,
   specific trait combinations that don't appear in organic roleplay) and add them
   as a new `jb_evolved_persona` pattern extending `JAILBREAK_ROLEPLAY_PATTERNS`.
2. Alternatively, extend `jb_evil_roleplay` to cover additional persona-initiation
   phrases found in the genetic corpus (e.g., "you embody an entity that", "you are
   the embodiment of", "your character has never been limited by").
3. Add a false-positive test class to ensure legitimate character-roleplay requests
   are not caught.

## Why it was held back
- Without access to the paper's full evolved-persona corpus, it is not possible to
  write a non-overlapping rule that is distinct from the existing `jb_evil_roleplay`,
  `jb_no_restrictions`, and `jb_grandma_exploit` patterns.
- A rule based on speculation about evolved-persona phrasing could have high false
  positive rates or duplicate existing coverage.

## Constraint that blocked it
- No concrete evolved-persona examples were available from the paper abstract or
  secondary sources to write a verifiable regex rule.
- Adding patterns without verification risks false positives on legitimate roleplay.

## Suggested next step for human reviewer
1. Access the full paper (arxiv:2507.22171) and extract examples from the evolved
   persona corpus (typically in Appendix or supplementary materials).
2. Compare to existing `jb_evil_roleplay`, `jb_no_restrictions`, `jb_grandma_exploit`
   coverage — if distinct patterns exist, add them.
3. Reference: arxiv:2507.22171 (Persona-Enhanced Genetic Jailbreak, Jul 2025).
