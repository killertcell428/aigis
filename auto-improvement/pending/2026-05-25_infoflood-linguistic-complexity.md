# Pending: InfoFlood — Information Overload Jailbreak Detection

## Title
Hardening guide and research note for the InfoFlood linguistic-complexity jailbreak technique

## Motivation
InfoFlood (Yadav et al., arxiv:2506.12274, Jun 2025) discovers that transforming harmful
queries into "information-overloaded" versions — using long relative clauses, nested
qualifications, archaic vocabulary, and layered rhetorical structures — can bypass LLM
safety evaluations without any adversarial prefix or harmful keyword. The attack exploits
the fact that safety classifiers are trained predominantly on direct, clear harmful
requests, and struggle when the same intent is wrapped in extreme linguistic complexity.
This was validated against multiple state-of-the-art safety-aligned LLMs.

## Research finding that led to this idea
Research file: `auto-improvement/research/2026-05-25T09-02_3-jailbreak-extraction.md`
- Finding: InfoFlood jailbreak (arxiv:2506.12274)

## Proposed change
1. Write a hardening guide under `docs/infoflood-complexity-bypass.md` documenting:
   - What the attack is and how it works (complexity as a safety-bypass vector)
   - Why token length limits alone (already in TOKEN_EXHAUSTION_PATTERNS) are insufficient
   - Mitigations operators can apply (complexity scoring, paraphrase normalisation before
     safety checking, or decomposition into sub-queries)
2. If a lightweight heuristic can be found (e.g., ratio of subordinate clause markers to
   total sentence count, or per-sentence word count variance), add a low-score input rule
   (`jb_complexity_overload`, score ~35) to flag pathologically complex single-sentence
   prompts. This would require empirical tuning against the AdvBench test set.

## Why it was held back
- The core bypass vector is statistical: "excessive linguistic complexity" has no
  single-token or phrase-level regex signal.
- A naive rule (flag long sentences) would have catastrophic false positive rates
  on legitimate legal, academic, or technical queries.
- Proper detection requires a sentence-complexity scorer (e.g., Flesch-Kincaid grade
  level, dependency-tree depth, or avg. clause count per sentence) which is not
  available within aigis's zero-runtime-dependency constraint.

## Constraint that blocked it
- Zero-runtime-dependency architecture: any complexity scorer requires NLTK, spaCy,
  or similar — not allowed as a required runtime dependency.
- > 100 LOC risk if implementing even a lightweight parser.

## Suggested next step for human reviewer
1. Evaluate whether a `dev`-extra dependency (e.g., minimal regex-based sentence
   splitter) could provide a useful approximation.
2. At minimum, write the `docs/infoflood-complexity-bypass.md` hardening guide —
   this is documentation-only and has no LOC or dependency constraints.
3. Reference: arxiv:2506.12274 (InfoFlood, Jun 2025).
