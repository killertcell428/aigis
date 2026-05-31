# Pending: RoleBreaker Character Hallucination Jailbreak

## Title
Multi-turn Character Hallucination Defense (RoleBreaker)

## Motivation
RoleBreaker (arXiv:2409.16727, Sept 2024; updated 2025) exploits "character hallucination" in
LLM role-playing systems: when a defined persona is stressed via query sparsity (sparse,
under-specified character definition) or role-query conflict (questions that conflict with the
assigned role), the model deviates from its persona and produces harmful outputs. Achieves 87.3%
average jailbreak success rate on 7 open-source LLMs; 84.3% on GPT-4.1, GLM-4, Gemini-2.0.

## Research Finding
arXiv:2409.16727 (Ruijie Quan et al., Sept 2024, updated 2025). Two driving factors:
query sparsity and role-query conflict. Defense: "Narrator Mode" (supplemental narrative context).

## Proposed Change
Two options:
1. Add test cases that codify known character hallucination trigger patterns as regression tests
   for the existing `jb_evil_roleplay` and `jb_grandma_exploit` rules (partial coverage).
2. Add a documentation guide under `docs/security/roleplay-jailbreaks.md` covering character
   hallucination with mitigations: defining characters explicitly, using Narrator Mode framing,
   and applying both input AND output scanning.

## Why Held Back
Character hallucination is an adaptive multi-turn attack driven by cumulative context, not a
single detectable prompt pattern. The deviation happens implicitly through accumulated
role-query conflicts rather than through a jailbreak phrase. Single-input regex cannot detect
this without semantic understanding of whether a query conflicts with an established persona.

## Constraint
Multi-turn behavioral detection required. Single-pass regex is insufficient.

## Suggested Next Step
When a session-level context tracker is implemented, add role-query conflict as a tracked signal.
In the interim, add a documentation entry explaining RoleBreaker-style attacks and recommending
that operators: (1) fully specify persona constraints in the system prompt, (2) scan outputs in
addition to inputs, and (3) use Narrator Mode (external narrative wrapper) for role-playing
deployments.
