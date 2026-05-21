# Pending: Multilingual Low-Resource Language Jailbreak Documentation

**Date:** 2026-05-21
**Research finding:** auto-improvement/research/2026-05-21T09-07_3-jailbreak-extraction.md (finding 5)
**Constraint blocking:** Requires language detection at input layer; not detectable via content regex.

---

## Title

Document multilingual jailbreak risk and guidance for low-resource language safety gaps.

## Motivation

arxiv:2605.18239 (Stellenbosch University, May 18, 2026) demonstrated that multi-turn conversations
in low-resource African languages (Afrikaans, Kiswahili, isiXhosa, isiZulu) bypass safety mechanisms
in commercial LLMs. Single-turn translation attacks are ineffective, but multi-turn achieves 52.7%
(Claude 3.5 Haiku) to 83.6% (GPT-4o-mini) harmful response rates. Human red-teaming raises average
ASR from 59.8% to 75.8%. The attack is a semantic one — the safety training is English-centric and
low-resource language variants bypass English-language safety rules.

## Proposed Change

Add a documentation file `docs/multilingual-jailbreak-risks.md` or a section in
`docs/hardening-guide.md` that:
1. Explains why English-only safety testing creates "the illusion of safety" for multilingual deployments
2. Lists documented high-risk language families for LLM safety gaps (low-resource African, South Asian)
3. Recommends red-teaming in the target deployment languages, not just English
4. Suggests language-detection pre-filters that flag unexpected script mixing as a risk signal
5. Notes the limitation: the current aigis pattern-based approach cannot substitute for
   multilingual safety training

## Why Deferred

- Cannot be addressed by regex patterns — the attack is semantic, not structural
- Documentation-only output needs proper doc structure and links to existing guides
- Low-urgency: the attack requires multi-turn interaction, reducing practical aigis-layer
  impact compared to single-turn attacks

## Suggested Next Step

Add documentation in a compliance-regulation or documentation-focused cycle.
