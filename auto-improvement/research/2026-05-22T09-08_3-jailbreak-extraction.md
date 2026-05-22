# Research: jailbreak-extraction — 2026-05-22T09-08

## Domain: jailbreak-extraction (index 3, fourth pass)
## Cycle index: 3
## Cycle timestamp: 2026-05-22T09-08

Prior cycles covered:
- Pass 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Pass 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Pass 3 (2026-05-13): Structured JSON/Dict System-Prompt Extraction, Sandwich Attack with verbatim qualifier.

This pass targets adversarial creative-format jailbreaks and single-message payload splitting, both deferred from pass 2, plus fresh research on multilingual and representation-level bypass techniques.

---

## Findings

- **Adversarial Poetry / Creative Format Jailbreak (arxiv:2511.15304, November 2025)**: Encoding
  harmful requests in poetic form achieves 62% average attack success rate across 25 frontier
  models (Google, OpenAI, Anthropic, DeepSeek, xAI, Meta) using hand-crafted adversarial poems,
  and 43% ASR with an automated meta-prompt that converts any of the MLCommons 1,200 harmful
  prompts into verse with no manual effort. Covered by The Register ("LLMs can be easily
  jailbroken using poetry"). The existing `jb_fictional_bypass` pattern misses long-form poetry
  requests because it uses a 100-character window and poetry directives often place the harmful
  topic further into the sentence (e.g. "Write a ballad in the style of William Blake, in four
  stanzas, describing the synthesis of…").
  - Source: https://arxiv.org/abs/2511.15304
  - **aigis takeaway:** Add `jb_poetry_harmful_framing` covering creative-format directive
    (write/compose/create + poem/rap/ballad/song/etc.) + harmful topic within 200 characters.
    **(IMPLEMENTED)**

- **Payload Splitting / Speak Easy (ICML 2025, arxiv:2502.04322, February 2025)**: Decomposes a
  harmful request into a sequence of numbered innocuous sub-queries where no single step triggers
  safety filters. Across benchmarks, GPT-4o's attack success rate increases from 9.2% to 55.5%;
  combined with multilingual translation (TAP-T), the rate exceeds 90%. The key structural
  signal: a prompt contains at least three numbered steps (Step 1, Step 2, Step 3) and the
  dangerous topic keyword appears in step 3 or later, while steps 1 and 2 are benign.
  - Source: https://arxiv.org/abs/2502.04322
  - **aigis takeaway:** Add `jb_payload_splitting` covering three-or-more numbered steps with a
    dangerous keyword in the third-or-later step. **(IMPLEMENTED)**

- **Multilingual Refusal Bypass via Language Transfer (arxiv:2505.17306, May 2025)**: Safety
  alignment transfers across languages via high-parallelism multilingual activation spaces, but
  safety training data is heavily skewed toward English. Identical harmful requests posed in
  low-resource languages (Swahili, Turkish, Vietnamese) achieve 10–30% refusal rates compared to
  ~90% refusal for English. The bypass doesn't require any special framing — just posing the
  harmful request in the low-resource language is sufficient.
  - Source: https://arxiv.org/abs/2505.17306
  - **aigis takeaway:** Rule-based detection on non-English input is difficult (legitimate
    multilingual use is valid). This strengthens the case for language-aware output monitoring
    rather than input-side regex. Noted for future compliance or hardening guide.

- **Activation Space Jailbreak Suppression — COSMIC (ACL 2025, arxiv:2506.00085, June 2025)**:
  Identifies refusal direction vectors in model activation space using cosine similarity. Once
  the refusal direction is found, attackers suppress it through weight orthogonalization or
  probabilistic ablation, achieving near-100% harmful output compliance. This operates entirely
  at the representation layer — no prompt-text pattern is detectable.
  - Source: https://arxiv.org/abs/2506.00085
  - **aigis takeaway:** Cannot be detected by rule-based regex input filter. Confirms that
    rule-based coverage breadth (reducing exploitable surface) is the correct strategy for
    proxy/firewall systems. Not implementable this cycle.

- **Embodied AI Jailbreaking — Action-Level Manipulation (arxiv:2603.01414, March 2026)**:
  Targets LLM-controlled robotic systems by exploiting misalignment between linguistic outputs
  and physical actions. Over 65% of adversarial prompts bypass defenses when integrated with
  GPT-4o; exceeds 90% ASR in some robot simulators. The attack exploits the gap between safe
  language output and unsafe action mapping.
  - Source: https://arxiv.org/abs/2603.01414
  - **aigis takeaway:** Requires action-semantic analysis, not prompt-text matching. Outside
    scope for current rule-based input/output filter. Relevant for future agentic action
    monitor module.

- **Concept Cones: Multi-dimensional Refusal Geometry (arxiv:2502.17420, February 2025)**:
  Refusal mechanisms are governed by multi-dimensional concept cones with functionally
  independent axes, not a single refusal direction. Attackers can target individual dimensions
  rather than attempting to suppress a monolithic refusal signal. Demonstrates that monolithic
  safety-steering (e.g. CAA) is easier to bypass than conal defenses.
  - Source: https://arxiv.org/abs/2502.17420
  - **aigis takeaway:** Not detectable by prompt-text regex. Reinforces multi-layer defense
    approach. Architecture insight for future safety spec documentation.

- **Internal Representation Jailbreak Detection and Evasion (arxiv:2602.11495, February 2026)**:
  Jailbreak attempts leave identifiable signatures in internal model hidden states. Detection
  methods achieve high accuracy using layer-wise analysis. The inverse implication: adversaries
  who know the detection method can craft "stealth" prompts that minimize the internal
  representation anomaly while still conveying harmful intent through novel linguistic forms
  not present in training.
  - Source: https://arxiv.org/abs/2602.11495
  - **aigis takeaway:** Rule coverage breadth and diversity remains the correct direction for
    rule-based systems. Not directly implementable this cycle.

---

## Candidate Hardenings

1. **`jb_poetry_harmful_framing`** (input, score 55) — Creative-format directive + harmful topic
   within 200 chars. Deferred from pass 2 due to LOC budget.
   → **IMPLEMENTED this cycle**

2. **`jb_payload_splitting`** (input, score 45) — Three-or-more numbered steps + dangerous
   keyword in step 3+. Deferred from pass 2 due to LOC budget.
   → **IMPLEMENTED this cycle**

3. *(pending)* Multilingual bypass — input language detection for rule-based filter is
   impractical; recommend output-side language-conditional scoring in future compliance cycle.

4. *(pending)* COSMIC / activation-space suppression — not detectable by regex; requires
   model internals access or output behavioral monitoring.

5. *(pending)* Embodied/action-level jailbreaking — requires action-semantic monitor, not
   prompt-text filter. Relevant for future agentic-action hardening module.
