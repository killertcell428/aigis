# Research: jailbreak-extraction — 2026-05-26T03-13

## Domain: jailbreak-extraction (index 3, fourth pass)
## Focus: Payload splitting, adversarial poetry, and chat-template special-token injection

Prior cycles covered:
- Cycle pass 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Cycle pass 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Cycle pass 3 (2026-05-13): Structured JSON/dict extraction, Extended sandwich attack, ICE, PHISH persona manipulation.

This pass targets three distinct angles not yet covered by deployed rules:
payload splitting / step decomposition, adversarial poetry framing, and chat-template
special-token injection.

---

## Findings

- **Speak Easy / Payload Splitting (arxiv:2502.04322, ICML 2025)**: Decomposing a harmful
  request into multiple numbered sub-queries — each appearing innocuous on its own — increases
  the average Attack Success Rate by 0.319 (absolute) across open-source and proprietary LLMs.
  Combined with multilingual translation of individual sub-steps, ASR on GPT-4o increases from
  0.092 to 0.555 and exceeds 0.9 when combined with the TAP-T jailbreaker. Because no single
  step contains the full harmful request, safety filters that evaluate each turn or sub-query
  in isolation fail to catch it. When embedded in a single prompt (all steps in one message),
  the dangerous keyword or action emerges only in step 3 or later, after plausibly benign setup
  steps.
  - Source: https://arxiv.org/abs/2502.04322
  - **aigis takeaway:** Add `jb_payload_splitting` pattern covering numbered steps (step N /
    part N / phase N) where a dangerous keyword appears in step 3+. This catches the single-turn
    form of the attack. (**CANDIDATE FOR IMPLEMENTATION**)

- **Adversarial Poetry as Universal Single-Turn Jailbreak (arxiv:2511.15304, Nov 2025)**:
  Encoding a harmful request inside a poem/rap/ballad directive achieves 62% average ASR across
  25 frontier models (hand-crafted poems) and 43% ASR with an automated meta-prompt that
  converts any of the 1,200 MLCommons harmful prompts to verse. ASR is up to 18× higher than
  the prose baseline for the same harmful request. The attack is single-turn, requires no
  multi-turn conversation, and transfers across CBRN, manipulation, cyber-offence, and
  loss-of-control domains. The existing `jb_fictional_bypass` pattern (which requires a
  fictional-world keyword within 100 chars of a dangerous keyword) does not catch "write a
  ballad describing in detail how to synthesize..." where the dangerous keyword sits 200+
  characters into the directive.
  - Source: https://arxiv.org/abs/2511.15304
  - **aigis takeaway:** Add `jb_poetry_harmful_framing` pattern: creative-format directive
    (poem/rap/ballad/song) + dangerous how-to or substance keyword within 200 chars.
    (**CANDIDATE FOR IMPLEMENTATION**)

- **MetaBreak: Chat-Template Special-Token Injection (arxiv:2510.10271, Oct 2025)**:
  LLM chat templates rely on special tokens — `<|im_start|>`, `[INST]`, `[/INST]`,
  `<|eot_id|>`, `<|start_header_id|>`, `<<SYS>>`, `<s>` — to delimit speaker turns.
  MetaBreak shows that injecting these tokens into user input allows three attack primitives:
  Response Injection (forge an affirmative assistant turn at the input stage), Turn Masking
  (hide injected content from text-based moderators), and Input Segmentation (split keywords
  across token boundaries to evade keyword filters). Against content moderation systems,
  MetaBreak outperforms state-of-the-art jailbreaks PAP and GPTFuzzer by 11.6% and 34.8%
  respectively. The existing `jb_affirmative_prefill` rule covers text-based role-marker
  injection ("Assistant: Sure, here is...") but does not cover the special-token form which
  looks structurally different and targets tokenizer-level parsing.
  - Source: https://arxiv.org/abs/2510.10271
  - **aigis takeaway:** Add `jb_chat_template_injection` pattern: presence of known chat-template
    special tokens (e.g. `<|im_start|>`, `[INST]`, `<<SYS>>`) in user input. (**CANDIDATE FOR
    IMPLEMENTATION**)

- **DrAttack: Prompt Decomposition and Reconstruction (arxiv:2402.16914)**: Decomposing a
  harmful prompt into separated sub-prompts and using in-context learning to reassemble them
  achieves >80% ASR on GPT-4 in human evaluation, surpassing prior SOTA by 65% absolute. The
  decomposition step is the key evasion mechanism — each fragment passes content filters because
  it contains no complete harmful instruction.
  - Source: https://arxiv.org/abs/2402.16914
  - **aigis takeaway:** Corroborates Speak Easy: numbered decomposition in single prompts is
    a reliable evasion technique. No additional new pattern needed beyond `jb_payload_splitting`.

- **Persona Prompt Genetic Optimization (arxiv:2507.22171)**: Genetic algorithm automatically
  evolves persona prompts to reduce LLM refusal rates by 50–70%. The evolved prompts are often
  natural-sounding role descriptions that do not match simple keyword patterns; they rely on
  semantic weight, not explicit jailbreak phrases.
  - Source: https://arxiv.org/abs/2507.22171
  - **aigis takeaway:** Semantic/behavioral detection required; not regex-detectable in
    single-turn mode. Confirms that persona-based jailbreaks are better handled via output
    scanning and behavioral aggregation than input keyword rules.

- **Re-Triggering Safeguards via Embedding Disruption (arxiv:2605.10611, May 2026)**:
  Proposes a defense that embeds a disruption perturbation into jailbreak inputs to re-activate
  model safeguards. Relevant as a defense technique; not an attack surface for aigis. Confirms
  that the rule-based approach (blocking known attack phrasings at input) remains complementary
  to gradient-based embedding-level defenses.
  - Source: https://arxiv.org/abs/2605.10611
  - **aigis takeaway:** Informational — confirms aigis rule coverage is complementary to
    model-level defenses, not a replacement.

---

## Candidate Hardenings

1. **`jb_payload_splitting`** (input, score 45) — Numbered step decomposition (step/part/phase
   1...2...3+) where a dangerous keyword appears in step 3+. Catches the single-turn embedded
   form of Speak Easy (ICML 2025) and DrAttack. False-positive risk: moderate (legitimate
   multi-step instructions exist); score of 45 means it needs co-occurring signals for HIGH.
   **→ IMPLEMENT THIS CYCLE**

2. **`jb_poetry_harmful_framing`** (input, score 55) — Creative-format directive (poem, rap,
   ballad, song, haiku, etc.) combined with a dangerous how-to instruction or substance keyword
   within 200 chars. 62% ASR (hand-crafted) / 43% ASR (automated) across 25 frontier models
   (arxiv:2511.15304). The existing `jb_fictional_bypass` does not cover this with its 100-char
   window. **→ IMPLEMENT THIS CYCLE**

3. **`jb_chat_template_injection`** (input, score 70) — Presence of well-known chat-template
   special tokens (`<|im_start|>`, `[INST]`, `<<SYS>>`, `<|eot_id|>`, etc.) in user-supplied
   input. Catches the MetaBreak attack class (arxiv:2510.10271) that bypasses text-based
   moderators by exploiting tokenizer template structure. Low false-positive rate in production:
   these tokens never appear in legitimate user input. **→ IMPLEMENT THIS CYCLE**

4. *(informational)* Semantic/behavioral persona optimization — multi-turn and gradient-level;
   not regex-detectable. No pending proposal; document only.
