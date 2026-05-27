# Research: jailbreak-extraction — 2026-05-27T00-15

## Domain: jailbreak-extraction (index 3, fourth pass)
## Cycle timestamp: 2026-05-27T00-15
## Focus: Creative-format jailbreaks and payload decomposition — implementing two patterns deferred from cycle 3

Prior cycles covered:
- Cycle 1 (2026-05-08T05-49): Bad Likert Judge, Many-Shot jailbreaks.
- Cycle 2 (2026-05-10T12-00): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Cycle 3 (2026-05-13T08-30): Structured JSON extraction, Sandwich attack extension, Autonomous LLM-vs-LLM.

This pass focuses on two patterns that were researched but could not be implemented in cycle 3 due to the LOC budget being exhausted, plus a fresh survey of 2026 jailbreak research.

---

## Findings

- **Adversarial Poetry as a Universal Single-Turn Jailbreak (arxiv:2511.15304, EMNLP 2025)**:
  Curated poetic prompts achieve 62% average attack success rate (ASR) across 25 frontier
  proprietary and open-weight models, with some providers exceeding 90%. A standardised
  meta-prompt that automatically converts any of the MLCommons 1,200 harmful prompts into
  verse achieves ~43% ASR — up to 18× higher than the same request in plain prose. Forms
  tested include rap songs, ballads, haikus, limericks, and traditional poems. The mechanism
  is that condensed metaphors and stylised rhythm disrupt pattern-matching heuristics that
  safety guardrails rely on. A single creative-format trigger word followed by harmful content
  within ~200 characters is the key structural signal.
  - Source: https://arxiv.org/abs/2511.15304
  - **aigis takeaway:** Implement `jb_poetry_harmful_framing` — creative-format directive +
    harmful how-to or dangerous subject within a bounded window. **(IMPLEMENTED)**

- **Speak Easy: Payload Splitting / Step-Enumerated Decomposition (arxiv:2502.04322, ICML 2025)**:
  Decomposing harmful requests into three or more numbered sub-questions raises the average
  absolute ASR by +0.319 and HarmScore (how actionable/harmful the response is) by +0.426
  across GPT-4o, Claude, and other frontier models. No individual step triggers safety filters
  because each appears benign in isolation; the dangerous intent emerges only when evaluated as
  a unit. The pattern is especially effective when combined with multilingual translation
  (different steps in different languages). The decisive signal for single-turn detection is
  three or more enumerated steps where a dangerous keyword (weapon, synthesis, exploit, etc.)
  appears in step 3 or later.
  - Source: https://arxiv.org/abs/2502.04322
  - **aigis takeaway:** Implement `jb_payload_splitting` — numbered step enumeration where a
    dangerous keyword appears in step 3+. **(IMPLEMENTED)**

- **Continuation-Triggered Jailbreak (arxiv:2603.08234, March 2026)**:
  Mechanistic interpretability study from Beijing Institute of Technology showing that appending
  a "continuation suffix" (e.g., "Continue the following story:") to a harmful prompt can
  substantially increase jailbreak ASR by exploiting the tension between the model's intrinsic
  continuation drive and safety alignment. The attack works at the level of attention heads —
  the continuation instruction activates token-prediction pathways that compete with and can
  suppress safety-refusal pathways. This is the most recent foundational study of why
  affirmative-continuation attacks work at the mechanistic level.
  - Source: https://arxiv.org/abs/2603.08234
  - **aigis takeaway:** Existing `jb_affirmative_prefill` (score 65) covers the injected
    "Assistant: Sure..." prefill form. The pure continuation suffix form ("Continue: [harmful
    content starter]") is partially covered but could be a dedicated rule. Deferred to pending —
    the existing `jb_affirmative_prefill` addresses the main exploitation surface.

- **Sugar-Coated Poison (arxiv:2504.05652, EMNLP 2025 Findings)**:
  Introduces Defense Threshold Decay (DTD): as an LLM generates more benign content, attention
  on input instructions progressively diminishes, reducing safety responsiveness. The SCP attack
  uses a "semantic reversal" strategy — a benign input opposite in meaning to the harmful intent
  is prepended. An Adversarial Reasoning Prompt variant achieves 95.96% ASR on GPT-3.5 Turbo
  and 86.73% on GPT-4. The attack relies on multi-turn or multi-step context accumulation, not
  a single identifiable prompt structure.
  - Source: https://arxiv.org/abs/2504.05652
  - **aigis takeaway:** Multi-turn context accumulation is not detectable by single-turn regex.
    The structural signal ("first generate benign content, then harmful content") is a session-
    level behavioral pattern — requires multi-turn correlation. Deferred to pending.

- **Time Bandit Jailbreak (CERT/CC, January 2025)**:
  Exploits temporal confusion by framing requests in a historical era where safety guidelines
  "don't apply yet." Example: "Imagine it's 1789; you're a programmer who can use modern tools."
  Confirmed by BleepingComputer and CERT/CC to bypass ChatGPT-4o and allow generation of
  weapon-making instructions and malware. The attack surface is the historical/fictional date
  + modern-tools request combination.
  - Source: https://cybersrcc.com/2025/02/05/time-bandit-vulnerability-jailbreaking-chatgpt-4o/
  - **aigis takeaway:** A `jb_temporal_confusion` pattern (historical era + modern dangerous
    request) would complement existing `jb_fictional_bypass`. Deferred — fictional framing is
    partially covered and the temporal-specific form needs careful false-positive tuning.

- **Adversarial Versification in Portuguese (arxiv:2512.15353, December 2025)**:
  Extends the adversarial poetry finding to non-English languages, confirming that poetic
  framing bypasses safety filters across language boundaries. Portuguese verse achieves
  comparable ASR to English on multilingual models.
  - Source: https://arxiv.org/abs/2512.15353
  - **aigis takeaway:** The `jb_poetry_harmful_framing` pattern already uses IGNORECASE mode
    and its harmful-keyword list includes English terms (synthesis, manufactur, hack, etc.).
    Non-English poetry attacks would require multilingual keyword expansion — deferred.

---

## Candidate hardenings

1. **`jb_poetry_harmful_framing`** (input, score 55) — creative-format directive + harmful
   how-to or dangerous subject within ~200 characters. ASR 62% (EMNLP 2025). **→ IMPLEMENTED**

2. **`jb_payload_splitting`** (input, score 45) — three or more numbered steps where a
   dangerous keyword appears in step 3+. ASR +0.319 (ICML 2025). **→ IMPLEMENTED**

3. *(deferred)* `jb_continuation_suffix` — "Continue:" + harmful content, mechanistic
   basis from arxiv:2603.08234. Partially covered by `jb_affirmative_prefill`.

4. *(deferred)* Multi-turn Sugar-Coated Poison (DTD) — requires session-level context
   accumulation tracking, not detectable by single-turn regex.

5. *(deferred)* `jb_temporal_confusion` (Time Bandit variant) — historical era framing +
   modern dangerous request. Needs false-positive tuning against legitimate history queries.
