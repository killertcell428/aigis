# Research: jailbreak-extraction — 2026-05-24T03-07

## Domain: jailbreak-extraction (index 3, fourth pass)
## Cycle timestamp: 2026-05-24T03-07

Prior passes covered:
- Pass 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Pass 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Pass 3 (2026-05-13): Structured JSON/dict extraction, Sandwich extraction (verbatim qualifier).

This pass targets adversarial poetry / creative-format jailbreaks, persona prompts, and
incremental completion decomposition — techniques documented in 2025–2026 research.

---

## Findings

- **Adversarial Poetry as Universal Single-Turn Jailbreak (arxiv:2511.15304v2, Nov 2025 / Jan 2026
  revision)**: Encoding harmful requests (CBRN, malware, manipulation) as poetry achieves an
  average 62% attack success rate (ASR) across 25 frontier models from Google, OpenAI,
  Anthropic, DeepSeek, Meta, xAI, Mistral, Moonshot AI, and Qwen. Converting 1,200 MLCommons
  harmful prompts into verse via a standardised meta-prompt produced ASR up to 18× higher than
  prose baselines. Cyber-offence prompts reached 84% ASR; CBRN prompts reached 68% ASR.
  The mechanism: condensed metaphors and stylistic framing disrupt the pattern-matching heuristics
  that safety guardrails rely on. Existing aigis jailbreak patterns only cover direct or
  framing-based attempts; they do not check for the combination of a creative-format directive
  (poem, rap, song, haiku, ballad, limerick) and a harmful topic keyword in the same input.
  - Source: https://arxiv.org/abs/2511.15304
  - **aigis takeaway:** Add `jb_poetry_harmful_framing` pattern. (**IMPLEMENTED**)

- **Adversarial Tales — Interpretability Research Agenda (arxiv:2601.08837, Jan 2026)**:
  Extension of the adversarial-poetry finding to story/narrative form. Shows the same bypass
  mechanism applies to requests phrased as short fictional tales. The structural signal that makes
  the attack detectable in single-turn context is still the co-occurrence of a narrative format
  keyword and a harmful topic.
  - Source: https://arxiv.org/abs/2601.08837
  - **aigis takeaway:** The `jb_poetry_harmful_framing` pattern also partially covers story-form
    variants (via the fictional framing overlap with `jb_fictional_bypass`). Story-specific terms
    (tale, story, narrative) could be a future extension.

- **Incremental Completion Decomposition (arxiv:2604.25921, April 2026)**: ICD is a
  trajectory-based jailbreak that first elicits single-word continuations related to a malicious
  request and then elicits the full response. Demonstrated superior ASR on AdvBench,
  JailbreakBench, and StrongREJECT vs. existing methods. This is inherently multi-turn and cannot
  be detected in a single-turn input filter.
  - Source: https://arxiv.org/abs/2604.25921
  - **aigis takeaway:** Requires session-level state tracking. Out of scope for rule-based
    single-turn detection. Send to pending.

- **Persona Prompts — Genetic Algorithm Optimisation (arxiv:2507.22171, July 2025)**: Evolved
  persona prompts reduce refusal rates by 50–70% across multiple LLMs and show synergistic
  effects when combined with existing attack methods (+10–20% ASR). The genetic algorithm
  produces prompts that are highly model-specific and not easily captured by fixed regexes.
  Partially covered by existing `jb_evil_roleplay` and `jb_hypothetical_ai` patterns; the
  evolved forms use subtler language not easily regex-detectable.
  - Source: https://arxiv.org/abs/2507.22171
  - **aigis takeaway:** No new regex-detectable pattern; behavioral detection needed. Noted.

- **RoguePrompt — Dual-Layer Ciphering (arxiv:2511.18790, Nov 2025)**: Combines two layers of
  ciphering so that neither layer alone encodes the harmful content, but the model reconstructs
  it during generation. Each layer uses different encoding (e.g., ROT13 + custom substitution).
  - Source: https://arxiv.org/abs/2511.18790
  - **aigis takeaway:** Multi-layer encoding detection partially covered by the evasion-
    obfuscation domain. The dual-layer pattern requires understanding of the decoding step, which
    is out of scope for input-only regex filtering. No new pattern this cycle.

- **Novel Cipher Attacks (arxiv:2402.10601v4, updated 2025)**: ACE (Attack using Custom
  Encryptions) and LACE (Layered ACE) encode harmful queries in novel user-created ciphers
  (keyboard cipher, upside-down cipher, word-reversal). LACE increases GPT-4 ASR from 40% to 78%.
  - Source: https://arxiv.org/abs/2402.10601
  - **aigis takeaway:** These attacks embed the harmful request in an encoding the model then
    decodes. The encoding surface is vast — regex cannot enumerate all custom ciphers. Covered
    conceptually by the evasion-obfuscation domain; no new jailbreak-extraction pattern.

- **Adversarial Versification in Portuguese (arxiv:2512.15353, Dec 2025)**: Confirms that
  adversarial poetry jailbreaks transfer across languages — Portuguese verse achieved similar
  ASR to English, confirming the bypass is structural rather than language-specific.
  - Source: https://arxiv.org/abs/2512.15353
  - **aigis takeaway:** Supports the priority of the `jb_poetry_harmful_framing` pattern. The
    harmful topic keywords in the regex are language-specific (English), but the poetry-format
    trigger words (poem, rap, song) are widely used in English-language attack prompts even when
    the verse content is in another language.

---

## Candidate Hardenings

1. **`jb_poetry_harmful_framing`** (input, score 60) — creative format directive (poem/rap/song/
   haiku/ballad/verse/lyrics/limerick/sonnet/rhyme/ode) co-occurring within 260 chars with a
   harmful topic keyword (explosives, synthesis, fentanyl, malware, nerve agent, bomb making,
   ransomware, bioweapon, chemical weapon). Covers the adversarial poetry jailbreak technique
   documented in arxiv:2511.15304 (62% average ASR across 25 frontier models). **→ IMPLEMENTED**

2. *(pending)* Incremental Completion Decomposition (ICD) — requires multi-turn session state.
   Regex-undetectable in single-turn mode.

3. *(pending)* Story/tale narrative form harmful framing — extension of `jb_poetry_harmful_framing`
   to cover short-story and fictional-tale format variants (arxiv:2601.08837). Requires care to
   avoid overlap with `jb_fictional_bypass`.

4. *(pending)* Evolved persona prompts (genetic-algorithm-generated) — no stable regex surface;
   behavioral detection required.
