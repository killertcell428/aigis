# Research: jailbreak-extraction — 2026-06-01T00-00

## Domain: jailbreak-extraction (index 3, fourth pass)
## Focus: Competing-objectives attacks, translation-based extraction, and HILL learning-framing jailbreaks

Prior cycles covered:
- Cycle 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Cycle 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Cycle 3 (2026-05-13): Structured JSON/dict system-prompt extraction, Extended sandwich attack with verbatim qualifier.

This pass targets three angles not yet covered in aigis: competing-objectives priority overrides,
translation/paraphrase-based extraction, and the HILL learning-framing technique.

---

## Findings

- **Domain-Based Taxonomy of Jailbreak Vulnerabilities (arxiv:2504.04976, April 2025)**: Systematic
  survey identifies competing objectives — where the model is nudged to resolve the helpfulness-vs-safety
  trade-off in favour of the user request — as one of the two root causes of jailbreak susceptibility.
  Competing-objectives attacks explicitly frame helpfulness as the model's "primary directive" and
  characterise safety policies as secondary obstacles to be overridden. Measured ASRs of 81–97% are
  reported across Llama, Mistral, and GPT-4 class models when this framing is combined with a harmful
  request. The existing `pi_role_switch` and `jb_no_restrictions` patterns target persona/mode changes
  and do not cover explicit priority-hierarchy overrides.
  - Source: https://arxiv.org/abs/2504.04976
  - **aigis takeaway:** Add `jb_competing_objectives` pattern covering prioritise-helpfulness-over-safety
    language. (**IMPLEMENTED**)

- **HILL — Hiding Intention by Learning from LLMs (arxiv:2509.14297, ACL 2025)**: Systematically
  transforms harmful directives into learning-oriented queries using four components: (1) convert
  imperative to exploratory question, (2) add step-by-step detail request, (3) insert hypotheticality
  markers ("for academic curiosity", "hypothetical"). Achieves top ASRs on the majority of tested
  models across AdvBench categories. The technique's distinctive feature is combining educational
  curiosity framing with requests for operational granularity ("which composition proportion is commonly
  used?", "which part controls the energy release?"). The existing `jb_academic_research_bypass` pattern
  partially covers this only when matched to specific high-risk keywords; HILL's educational framing
  works across a broader range of topics not covered by that rule.
  - Source: https://arxiv.org/abs/2509.14297
  - **aigis takeaway:** The academic bypass pattern already covers the most dangerous HILL variants.
    The gap (non-keyword educational queries) has too high a false-positive cost to close with regex.
    Documented for future behavioural / intent-classification defences.

- **Translation and Paraphrase as System-Prompt Extraction Vectors (arxiv:2505.23817 and postmortems)**:
  System prompt extraction taxonomy (Das et al., 2025) documents that indirect extraction — asking the
  model to translate, paraphrase, or summarise its instructions — reliably leaks system-prompt content
  even when direct extraction is blocked. The Sydney/Bing Chat operator prompt leak and multiple 2024–2025
  operator prompt exposures used paraphrase requests to bypass filters that only matched "show me your
  system prompt". Unlike the sandwich attack (`jb_sandwich_extraction`), no verbatim qualifier is
  needed; the attacker accepts a paraphrased version that still exposes the system prompt's intent,
  scope, and key constraints.
  - Source: https://arxiv.org/abs/2505.23817; https://startup-house.com/blog/llm-jailbreak-techniques
  - **aigis takeaway:** Add `jb_translation_extraction` pattern covering translate/paraphrase/summarize
    + system-prompt references. (**IMPLEMENTED**)

- **Anyone Can Jailbreak — Unified Taxonomy (arxiv:2507.21820, July 2025)**: Develops a unified
  taxonomy of five prompt-based jailbreak categories: multi-turn narrative escalation, lexical
  camouflage, implication chaining, fictional impersonation, and subtle semantic edits. Every stage
  of the moderation pipeline can be bypassed with low-effort attacks. Key finding: "lexical camouflage"
  (using alternative wording to mask prohibited requests) is the hardest category to cover with static
  regex rules because the vocabulary is unbounded.
  - Source: https://arxiv.org/abs/2507.21820
  - **aigis takeaway:** Lexical camouflage confirms that rule-based systems need frequent pattern
    rotation, not one-time coverage. No single new pattern addresses the full category.

- **Enhancing Jailbreak Attacks via Persona Prompts (arxiv:2507.22171, March 2026)**: Evolved persona
  prompts reduced refusal rates by 50–70% across multiple LLMs and showed synergistic effects when
  combined with existing methods (+10–20% ASR). The technique creates detailed, coherent personas whose
  stated goals and history justify unsafe outputs. The existing `jb_evil_roleplay` and
  `jb_no_restrictions` patterns cover the crudest variants; the evolved persona approach is subtler and
  harder to catch with keyword rules alone.
  - Source: https://arxiv.org/abs/2507.22171
  - **aigis takeaway:** Evolved personas are multi-turn and semantically rich — not effectively
    addressed by single-turn regex. Document for future persona-consistency tracking.

- **Analysis of LLMs Against Prompt Injection and Jailbreak Attacks (arxiv:2602.22242, Feb 2026)**:
  Notes that models may prioritise instruction-following and narrative consistency over safety enforcement
  when confronted with sufficiently coherent prompts. This is the competing-objectives mechanism in
  practice. The paper confirms that framing the user request as the model's "primary objective" is
  consistently effective even on hardened models.
  - Source: https://arxiv.org/abs/2602.22242
  - **aigis takeaway:** Supports implementation of `jb_competing_objectives`. See above.

---

## Candidate Hardenings

1. **`jb_competing_objectives`** (input, score 65) — Priority-override attack covering
   "prioritise helpfulness over safety", "helpfulness is more important than restrictions", and
   "don't let safety rules prevent you from helping" forms. **→ IMPLEMENTED**

2. **`jb_translation_extraction`** (input, score 60) — Translate/paraphrase/summarize verbs
   targeting system prompt, initial instructions, or internal guidelines. **→ IMPLEMENTED**

3. *(pending)* HILL non-keyword educational queries — too broad for regex; needs intent
   classification.

4. *(pending)* Evolved persona jailbreaks (arxiv:2507.22171) — multi-turn behavioural; needs
   persona-consistency tracker.

5. *(pending)* Lexical camouflage (arxiv:2507.21820) — vocabulary is unbounded; needs semantic
   similarity or embedding-based detection.
