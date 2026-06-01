# Pending: HILL Educational-Framing Non-Keyword Detection

## Title
HILL-style learning-framing jailbreak detection without harmful-keyword dependency

## Motivation
The HILL (Hiding Intention by Learning from LLMs) framework (arxiv:2509.14297, ACL 2025) transforms
harmful requests into educational curiosity questions by combining:
1. Exploratory phrasing ("What is X like?") instead of directives ("Explain how to do X")
2. Granular detail requests ("Which part controls the energy release? What composition proportion?")
3. Hypotheticality markers ("for academic curiosity", "hypothetical")

The current `jb_academic_research_bypass` rule covers HILL variants that target specific harmful
keywords (drug synthesis, weapon construction, exploit code). HILL's strength is that it also
works for harmful topics that don't match those keywords — the same reframing pattern applied to
less-obvious harmful content still achieves high ASR.

## Proposed change
Add a pattern that detects "educational curiosity + operational step-by-step detail" framing
without requiring the specific harmful-keyword anchor used by `jb_academic_research_bypass`.

## Why it was held back
The combination of ("for academic curiosity" OR "as a curious learner") + "step by step" OR
"composition" OR "proportion" OR "how does X work" without additional anchoring has extremely
high false-positive rate. Legitimate educational queries ("For academic curiosity, how does a
transformer model process tokens step by step?") match the pattern perfectly. Reducing
false positives to acceptable levels requires semantic intent classification, not regex.

## Which constraint blocked it
Regex-only rule with unacceptable false-positive rate. Violates the "do not add features that
depend on calling an LLM at runtime" constraint if solved correctly with intent classification.

## Research finding
arxiv:2509.14297 (HILL, ACL 2025): https://arxiv.org/abs/2509.14297

## Suggested next step
Implement as a second-stage intent classifier (non-LLM) that activates only when
`jb_academic_research_bypass` fires but score is below the block threshold, or when a score
from a lightweight text classifier trained on HILL-style jailbreak datasets exceeds a threshold.
Alternatively, expand the keyword list in `jb_academic_research_bypass` to cover more harmful
topic categories beyond the current drug/weapon/exploit set.
