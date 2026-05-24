# Pending: Evolved Persona Prompt Detection

## Title
Detection for genetic-algorithm-evolved persona jailbreak prompts

## Motivation
arxiv:2507.22171 ("Enhancing Jailbreak Attacks on LLMs via Persona Prompts", July 2025)
shows that a genetic algorithm can automatically evolve persona prompts that reduce refusal
rates by 50–70% across multiple LLMs. These evolved prompts also show synergistic effects
when combined with existing methods (+10–20% ASR). The evolved forms use subtler language
than "act as an evil AI" — they often frame the persona in terms of authority, expertise,
or domain-specific context that bypasses safety pattern matching.

## Why Held Back
Evolved persona prompts by definition do not have a stable regex surface — the genetic
algorithm optimises them specifically to avoid pattern-matching defences. No single regex
can enumerate the space of evolved prompts.

## Possible Approach
Semantic similarity scoring (e.g., cosine similarity between input and known-bad persona
templates) could flag evolved prompts. However, this would require a runtime dependency
on a similarity model or embedding API — violating aigis's zero-runtime-dependency rule.

## Constraint That Blocked It
Zero-runtime-dependency constraint. Semantic matching requires either a local embedding
model (new required dependency) or an external API call (network dependency at runtime).

## Suggested Next Step
Human reviewer: if aigis ever adopts a lightweight local embedding model as an optional
dependency (opt-in, not required), the evolved-persona case is a strong motivator for
semantic jailbreak detection. Until then, the best mitigation is breadth of coverage
across the known fixed-form jailbreak patterns already implemented.
