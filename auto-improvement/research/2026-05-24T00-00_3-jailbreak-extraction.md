# Research: jailbreak-extraction — 2026-05-24T00-00

## Domain: jailbreak-extraction (index 3, fourth pass)
## Cycle index: 3
## Cycle timestamp: 2026-05-24T00-00

Prior passes covered:
- Pass 1 (cycle 2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Pass 2 (cycle 2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Pass 3 (cycle 2026-05-13): Structured-output system-prompt extraction (JSON/YAML/dict),
  Sandwich attack verbatim qualifier, Autonomous LLM-vs-LLM jailbreaking.

This pass targets two gaps not covered by earlier passes:
1. Chat template token injection (sockpuppetting / MetaBreak) — a newer form of output-prefix injection.
2. Payload splitting (step-enumerated decomposition) — a pending idea from pass 2 that was deferred for LOC reasons.

---

## Findings

- **Sockpuppetting — Output Prefix Injection via Chat Template Tokens (arxiv:2601.13359, Jan 2026)**:
  Inserts an acceptance sequence directly into the `role=assistant` slot of the model's chat
  template, either via the API's `assistant` message prefill feature or by embedding raw
  model-specific special tokens (e.g. `<|im_start|>assistant`, `<|start_header_id|>assistant
  <|end_header_id|>`) in user-supplied text. The model, seeing tokens that mark the start of an
  assistant turn, continues the injected text as its own response. Ensemble of three prefill
  variants achieves 22%, 90%, and 99% ASR on Gemma-7B, Llama-3.1-8B, and Qwen3-8B respectively.
  No optimization pass is required — a single injected line suffices.
  - Source: https://arxiv.org/abs/2601.13359
  - **aigis takeaway:** Detect raw chat-template delimiter tokens in user-submitted text:
    `<|im_start|>`, `[/INST]`, `<<SYS>>`, `<|start_header_id|>assistant`, `<|assistant|>`,
    `<start_of_turn>model`. Legitimate users have no reason to embed these model-internal
    formatting tokens in plain input.

- **MetaBreak — Special Token Manipulation for Online LLMs (arxiv:2510.10271, Oct 2025)**:
  Systematically exploits chat-format special tokens against production LLM APIs. An attacker
  embeds a fake `assistant` turn using raw control tokens to inject an affirmative prefix before
  the actual request is evaluated, causing the model to treat the injection as prior context.
  Evaluated on GPT, Claude, and Gemini APIs. The paper shows that even APIs which claim to
  strip or escape special tokens sometimes fail to do so consistently.
  - Source: https://arxiv.org/abs/2510.10271
  - **aigis takeaway:** Reinforces the case for the `jb_chat_template_injection` pattern. The
    attacker embeds the same family of special tokens; catching them at the input-scan layer
    prevents the injection from reaching the model.

- **Payload Splitting / Speak Easy (arxiv:2502.04322, ICML 2025)**:
  Decomposes a harmful request into multiple numbered sub-queries, each individually benign.
  GPT-4o's ASR rises from 0.092 to 0.555; combined with multilingual translation (also part of
  the Speak Easy framework) it exceeds 0.9. The decomposition makes each step pass safety filters
  because no single step explicitly names the harmful goal. The dangerous topic emerges only when
  later steps are executed in sequence.
  - Source: https://arxiv.org/abs/2502.04322
  - **aigis takeaway:** Add `jb_payload_splitting`: detect three or more numbered
    step/part/phase/question entries in a single message where a dangerous topic keyword appears
    within step 3 or later. Pending since 2026-05-10 due to LOC budget; implementing this cycle.

- **PANDAS Many-Shot Jailbreaking (arxiv:2502.01925, Feb 2025)**:
  Enhances many-shot jailbreaking with Positive Affirmation (PA) — inserting "Sure, here is..."
  phrases before new malicious questions in fabricated dialogue — and Negative Demonstration (ND)
  — embedding refusal and correction phrases to train the model to reject refusals. PANDAS
  outperforms baseline many-shot across all datasets and models tested. Detection via text scanning
  is substantially covered by the existing `jb_many_shot` + `jb_affirmative_prefill` patterns,
  which together catch both the fabricated dialogue format and the affirmative prefixes.
  - Source: https://arxiv.org/abs/2502.01925
  - **aigis takeaway:** No new pattern needed; existing rules cover the PANDAS attack surface.
    Document the overlap as a coverage note.

- **Mitigating Many-Shot Jailbreak Attacks with One Single Demonstration (arxiv:2605.08277,
  May 2026)**:
  Defensive research showing that injecting a single benign refusal example before many-shot
  attack pairs can reduce ASR by up to 94%. Also demonstrates that many-shot attacks remain
  effective at 32-shot and above on GPT-4o, Claude 3 Sonnet, and Llama-3.1-70B. The paper
  confirms that the attack threshold (where MSJ becomes reliably effective) is around 8–16 shots.
  - Source: https://arxiv.org/abs/2605.08277
  - **aigis takeaway:** The existing `jb_many_shot` pattern (which requires 3+ faux dialogue
    pairs) correctly covers the minimum effective threshold. No pattern change needed, but good
    confirmation that the detection threshold is appropriate.

- **Virtual Context — Special Token Injection (arxiv:2406.19845, 2024)**:
  Earlier foundational work showing that injecting special tokens (BOS, EOS, role delimiters)
  in user input can create a "virtual context" — the model interprets the injected tokens as
  legitimate conversation boundaries and changes its behavior accordingly. Achieved 97% ASR on
  Llama-2 70B.
  - Source: https://arxiv.org/abs/2406.19845
  - **aigis takeaway:** Adds historical precedent for the `jb_chat_template_injection` pattern.
    The attack family has been known since 2024; this cycle implements detection.

---

## Candidate Hardenings

1. **`jb_chat_template_injection`** (input, score 75) — Detect raw chat-template delimiter tokens
   in user-submitted text: `<|im_start|>assistant`, `<|start_header_id|>assistant<|end_header_id|>`,
   `[/INST]`, `<<SYS>>`, `<|assistant|>`, `<start_of_turn>model`. These are model-internal
   formatting tokens that have no legitimate place in plain user input. Sockpuppetting
   (arxiv:2601.13359) and MetaBreak (arxiv:2510.10271) both rely on this technique.
   **→ IMPLEMENT THIS CYCLE**

2. **`jb_payload_splitting`** (input, score 45) — Detect three or more numbered step/part/phase
   entries in a single message where a dangerous topic keyword (chemical, explosive, hack, malware,
   etc.) appears within or after the third entry. Speak Easy (arxiv:2502.04322, ICML 2025) raises
   GPT-4o ASR from 9.2% to 55.5% using this technique. Previously pending due to LOC budget.
   **→ IMPLEMENT THIS CYCLE**

3. *(covered)* PANDAS many-shot — existing `jb_many_shot` + `jb_affirmative_prefill` cover the
   PANDAS attack surface.

4. *(pending)* Structural message-history validation — a new `validate_message_roles()` helper
   that checks the API messages array for injected `role=assistant` turns from user-controlled
   sources (sockpuppetting at the API level). Requires changes to `Guard.check_messages()` and
   input_filter.py; exceeds 100 LOC. See `2026-05-09_conversation-history-injection.md`.
