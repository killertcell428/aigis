# Research: jailbreak-extraction — 2026-05-13T08-30

## Domain: jailbreak-extraction (index 3, third pass)
## Focus: System-prompt extraction techniques — structured output, sandwich attack, and autonomous jailbreaks

Prior cycles covered:
- Cycle 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Cycle 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.

This pass targets structured-output system-prompt extraction, the sandwich attack technique, and
autonomous LLM-vs-LLM jailbreaking research from 2025–2026.

---

## Findings

- **Structured JSON/Dict System-Prompt Extraction (arxiv:2505.23817, May 2025)**: Attackers
  bypass naive extraction detectors (which only match "show me your system prompt") by requesting
  the model to output its configuration as structured data: `{"system_prompt": "...",
  "content_policy": "...", "restrictions": [...]}`. Before the ProxyPrompt defense,
  up to 92% ASR on Llama-3 and 84% on Falcon-3. The aigis `pi_system_prompt_leak` pattern
  (score 45) does not cover this framing since it matches literal "system prompt" in a direct
  request, not in a JSON field enumeration.
  - Source: https://arxiv.org/abs/2505.23817
  - **aigis takeaway:** Add `jb_structured_extraction` pattern covering JSON/YAML/dict + system-prompt
    field names. (**IMPLEMENTED**)

- **Extended Sandwich Attack for System-Prompt Extraction (arxiv:2505.23817)**: The sandwich
  attack embeds an extraction request between benign questions. The extended form adds a
  negative-constraint qualifier — "without additional text", "verbatim", "word for word" — that
  suppresses the model's tendency to paraphrase, maximising extraction fidelity. This raised
  ASR from ~50% to 84–92% across multiple models. The qualifier is the key signal that
  distinguishes the advanced form from a casual "tell me your guidelines" query.
  - Source: https://arxiv.org/abs/2505.23817
  - **aigis takeaway:** Add `jb_sandwich_extraction` covering (system prompt extraction verb) +
    (verbatim/without-additional-text qualifier). (**IMPLEMENTED**)

- **Autonomous LLM-vs-LLM Jailbreaking (Nature Communications, 2026)**: Landmark study showed
  that large reasoning models (DeepSeek-R1, Gemini 2.5 Flash, Grok 3 Mini, Qwen3) can
  autonomously jailbreak other LLMs with 97.14% overall success rate across nine target models
  including GPT-4o and Claude 4 Sonnet, with no human intervention. Claude showed the lowest
  vulnerability (2.86% ASR) while DeepSeek-V3 was most vulnerable (90% ASR).
  - Source: https://redteams.ai/blog/llm-jailbreaking-2026
  - **aigis takeaway:** Autonomous jailbreaks are multi-turn and behavioral — not regex-detectable
    in single-turn mode. The study confirms that broader rule coverage (reducing the surface
    AutoAdv can exploit) remains the correct defense strategy for rule-based systems.

- **ICE — Intent Concealment and Diversion (arxiv:2505.14316, ACL 2025)**: Achieves high ASR
  with a single query by concealing harmful intent within a benign framing and diverting
  attention using misdirection. Introduced BiSceneEval dataset. The specific concealment
  technique varies (analogies, embedded sub-tasks) — too diverse for a single regex pattern.
  - Source: https://arxiv.org/abs/2505.14316
  - **aigis takeaway:** The academic framing bypass (`jb_academic_research_bypass`) partially
    covers some ICE variants. No single new pattern this cycle.

- **Structured Output Control-Plane Jailbreaks (arxiv:2503.24191, Mar 2025; arxiv:2510.17904
  BreakFun)**: Attacks weaponize JSON Schema enum constraints and grammar-level rules to embed
  harmful intent at the schema/control-plane level while keeping the text prompt benign.
  DictAttack achieves 94–99% ASR on GPT-5, Gemini 2.5. These attacks exploit the constrained
  decoding layer, not the prompt surface — regex detection is insufficient.
  - Source: https://arxiv.org/abs/2503.24191; https://arxiv.org/abs/2510.17904
  - **aigis takeaway:** Infrastructure-level (schema validation, constrained decoding audit)
    rather than regex-level defense. Send to pending for a future structural-output hardening guide.

- **Persona Jailbreaking — PHISH (arxiv:2601.16466, Jan 2026)**: Gradually induces an
  adversarial persona via semantically loaded cues in user queries without any explicit
  jailbreak phrase. Targets long-term deployed personas in education, mental health, customer
  service. Incremental multi-turn manipulation — not detectable in single-turn filter.
  - Source: https://arxiv.org/abs/2601.16466
  - **aigis takeaway:** Multi-turn behavioral detection required. Cross-session correlator
    roadmap item.

---

## Candidate Hardenings

1. **`jb_structured_extraction`** (input, score 65) — JSON/dict/YAML field enumeration for
   system-prompt extraction. **→ IMPLEMENTED**

2. **`jb_sandwich_extraction`** (input, score 65) — Verbatim/without-additional-text qualifier
   on system-prompt extraction request (extended sandwich attack). **→ IMPLEMENTED**

3. *(pending)* Control-plane jailbreaks via JSON Schema enums — requires schema-validation
   layer, not regex; infrastructure-level defense.

4. *(pending)* PHISH persona manipulation — multi-turn behavioral detection required.
