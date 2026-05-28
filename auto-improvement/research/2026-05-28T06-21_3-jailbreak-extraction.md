# Research: jailbreak-extraction — 2026-05-28T06-21

## Domain: jailbreak-extraction (index 3, fourth pass)
## Cycle timestamp: 2026-05-28T06-21

Prior cycles covered:
- Cycle pass 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Cycle pass 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Cycle pass 3 (2026-05-13): Structured JSON/dict extraction, Extended sandwich extraction (verbatim qualifier).

This pass implements two pending patterns deferred since May 10 due to LOC budget constraints:
`jb_poetry_harmful_framing` and `jb_payload_splitting`.

---

## Findings

- **Adversarial Poetry as a Universal Single-Turn Jailbreak (arxiv:2511.15304, Nov 2025)**:
  Researchers at the University of Glasgow demonstrated that wrapping harmful requests in poetic
  form bypasses LLM safety filters at dramatically higher rates than prose. 20 hand-crafted
  adversarial poems achieved an average 62% attack success rate (ASR) across 25 frontier
  closed- and open-weight models, with some providers exceeding 90% ASR. A standardized
  meta-prompt that converts any of the 1,200 MLCommons harmful prompts into verse achieved
  43% ASR with no manual effort — roughly 5× the prose baseline. Covered by The Register, Dark
  Reading, and The Cyber Express. The attack works because models are trained to cooperate with
  creative writing tasks, while safety training was calibrated primarily on direct prose-style
  requests. The specific creative formats tested include poems, ballads, raps, and verse-form
  instructions.
  - Source: https://arxiv.org/abs/2511.15304
  - **aigis takeaway:** Add `jb_poetry_harmful_framing`: creative format directive (poem/rap/
    ballad/song/haiku/etc.) + harmful topic keyword within ~200 characters. (**IMPLEMENTED**)

- **Speak Easy — Payload Splitting via Multi-Step Decomposition (ICML 2025, arxiv:2502.04322,
  Feb 2025)**: Breaks a harmful request into multiple numbered sub-queries, each appearing
  innocuous in isolation. When SPEAK EASY is layered onto baseline jailbreak attacks, GPT-4o's
  ASR increases from 9.2% to 55.5%, and the HarmScore metric increases by 0.426 on average
  across four safety benchmarks and both open-source and proprietary LLMs. The technique
  emulates natural multi-step human reasoning to evade guards that evaluate single messages:
  step 1 asks about benign precursors, step 2 identifies a specific dangerous combination, and
  step 3 requests the synthesis or attack procedure.
  - Source: https://arxiv.org/abs/2502.04322
  - **aigis takeaway:** Add `jb_payload_splitting`: 3+ numbered steps (step/part/phase/task +
    digit) with a dangerous keyword in step 3+. (**IMPLEMENTED**)

- **Bypassing LLM Guardrails via Character Injection and AML Evasion (arxiv:2504.11168, Apr
  2025)**: Demonstrates that traditional character injection (inserting noise characters into
  harmful prompts) and adversarial machine learning techniques can evade six production
  guardrail systems including Microsoft Azure Prompt Shield and Meta Prompt Guard, achieving
  up to 100% evasion success in some configurations. The paper targets guardrail models rather
  than base LLMs, showing that regex-based and embedding-based defenses can be defeated with
  targeted perturbations. Both techniques maintain semantic "adversarial utility" (the LLM
  still produces harmful output) while evading detection.
  - Source: https://arxiv.org/abs/2504.11168
  - **aigis takeaway:** Character-injection evasion targets embedding-based guards, not rule-based
    regex systems. aigis's existing `te_unicode_noise`, `te_null_byte_stuffing`, and
    `te_unicode_tag_smuggling` patterns already cover the character injection forms most
    applicable to regex detection. No new rule this cycle.

- **SequentialBreak — Jailbreak via Sequential Prompt Chains (arxiv:2411.06426, Nov 2024)**:
  Hides harmful prompts inside a sequential context structure (Question Bank, Dialog Completion,
  or Game Environment scenario). The attack uses a single query, embeds the harmful request
  among benign surrounding content, and achieves a "substantial gain" in ASR over existing
  baselines against both open- and closed-source models. Context manipulation causes the model
  to focus on benign framing while processing the embedded harmful instruction.
  - Source: https://arxiv.org/abs/2411.06426
  - **aigis takeaway:** The technique is structurally similar to indirect injection patterns
    already covered by `ii_hidden_instruction`, `ii_delimiter_spoof`, and `jb_fictional_bypass`.
    No single additional regex captures the full sequential framing; noted for future multi-pass
    context scanning research.

- **Evolved Persona Prompts via Genetic Algorithm (arxiv:2507.22171)**:
  Automatically crafts persona prompts using crossover, mutation, and selection to reduce model
  refusal rates by 50–70% across multiple LLMs (Qwen2.5-14B, LLaMA-3.1-8B, DeepSeek-V3).
  Evolved prompts show synergistic effects when combined with existing attack methods,
  increasing overall ASR by 10–20%. The evolved prompts are model-specific and do not
  follow a fixed structural template — making them difficult to capture with a single regex.
  - Source: https://arxiv.org/abs/2507.22171
  - **aigis takeaway:** Evolution-based persona attacks produce varied forms not easily captured
    by regex. The existing `jb_evil_roleplay`, `jb_developer_mode`, and `jb_grandma_exploit`
    patterns cover the most common persona templates. Broader coverage would require a semantic
    classifier; send to pending.

- **JBFuzz — Fuzzing-Based Jailbreak Framework (~99% ASR)**: A fuzzing framework for
  automatically discovering jailbreak prompts. Achieved ~99% average ASR across GPT-4o, Gemini
  2.0 Flash, and DeepSeek-V3. Like AutoAdv and PAIR, success depends on iterative
  model-specific refinement rather than a fixed prompt structure, so no single regex captures it.
  The research confirms that broader rule coverage reduces the surface exploitable by automated
  jailbreak tools.
  - Source: https://startup-house.com/blog/llm-jailbreak-techniques
  - **aigis takeaway:** No new single-turn rule; reinforces the value of broad jailbreak
    pattern coverage across all categories.

---

## Candidate Hardenings

1. **`jb_poetry_harmful_framing`** (input, score 55) — creative format directive + harmful
   topic keyword within ~200 chars. **→ IMPLEMENTED**

2. **`jb_payload_splitting`** (input, score 45) — 3+ numbered steps with dangerous keyword
   in step 3+. **→ IMPLEMENTED**

3. *(pending)* SequentialBreak via Question Bank / Game Environment framing — partially covered
   by existing indirect injection patterns; single regex insufficient for full coverage.

4. *(pending)* Evolved persona prompts (genetic algorithm) — no fixed structure; would need
   semantic classifier rather than regex.

5. *(noted)* Character injection / AML evasion targeting guardrail models — covered by existing
   unicode noise and tag smuggling patterns for the regex-detectable surface.
