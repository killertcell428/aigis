# Pending: Multilingual Bypass Documentation Hardening Guide

**Title:** Multilingual Jailbreak Risk Guide for AI Agent Operators

**Motivation:**
A May 2026 study (arxiv:2605.18239) demonstrated that multi-turn conversations in low-resource
African languages (Afrikaans, Kiswahili, isiXhosa, isiZulu) achieve harmful response rates of
52.7–83.6% against commercial LLMs including GPT-4o, Claude, DeepSeek, Gemini, and Grok.
The root cause is that safety training concentrates on English, leaving low-resource languages
under-defended. Human red-teaming improved attack success rates by up to +20 percentage points
over automated translation, confirming intentional exploitation by adversaries.

**Research finding that led to this idea:**
`auto-improvement/research/2026-05-27T09-18_3-jailbreak-extraction.md`
→ "Multilingual Jailbreak via Low-Resource African Languages" finding

**Proposed change:**
Add `docs/multilingual-bypass-risks.md` documenting:
1. Overview of the multilingual bypass attack surface and why safety gaps exist
2. Risk matrix: which languages are most under-defended (low-resource / low RLHF coverage)
3. Compensating controls: input language detection, output-layer moderation, routing policies
4. Aigis integration advice: using language-detection preprocessing to flag unexpected language
   shifts, especially in agent pipelines where user language is predictable
5. Recommendations for operators using aigis in multilingual deployments

**Why it was held back:**
- This is a documentation deliverable, not a detection rule — implementing it is safe
- However, the guide requires careful research into which specific languages are most vulnerable
  and what tooling is available for language detection in Python without adding heavy deps
- Needed more time than the current cycle allows for a quality guide

**Which constraint blocked it:**
No hard constraint; held back due to cycle-length limits on research quality.

**Suggested next step for the human reviewer:**
A future cycle should draft `docs/multilingual-bypass-risks.md` with:
- Language detection options (langdetect, lingua-py as optional dev extras, or api-based)
- Specific language codes and their documented vulnerability levels
- Sample aigis middleware snippet that warns when user language switches unexpectedly
