# Research: jailbreak-extraction — 2026-05-30T09-13

## Domain: jailbreak-extraction (index 3, fourth pass)
## Cycle timestamp: 2026-05-30T09-13

Prior cycle 3 passes:
- Pass 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Pass 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Pass 3 (2026-05-13): Structured JSON extraction (`jb_structured_extraction`), Sandwich extraction (`jb_sandwich_extraction`).

This pass focuses on creative-format jailbreaks (adversarial poetry) and special / control token injection.

---

## Findings

- **Adversarial Poetry as a Universal Jailbreak (arxiv:2511.15304, November 2025)**:
  Encoding harmful requests in poetic form (rap songs, ballads, haiku) achieves 62% average
  attack success rate across 25 frontier models including GPT-4o, Claude 3, Gemini Pro,
  Llama 3, and Mistral. An automated meta-prompt that converts any of the MLCommons 1,200
  harmful prompts into verse achieves 43% ASR with no human effort. Covered by The Register.
  Up to 90%+ ASR for some providers. The technique is a single-turn attack, bypassing
  conversation-history defenses entirely.
  - Source: https://arxiv.org/abs/2511.15304
  - **aigis takeaway:** `jb_poetry_harmful_framing` (pending since 2026-05-10) is now
    implemented this cycle: creative-format verb + poem/rap/song type + harmful topic within
    ~200 chars. (**IMPLEMENTED**)

- **MetaBreak: Special Token Injection via Online LLM Services (arxiv:2510.10271, Oct 2025)**:
  Attackers inject model-specific control tokens — `<|system|>`, `<|im_start|>`, `<|endoftext|>`,
  `[INST]`, `<<SYS>>` — into user-supplied text. Many production deployments forward user text
  to the model without stripping these tokens, allowing injected role-boundary markers to
  override system prompt instructions. MetaBreak demonstrated successful safety bypasses on
  major online LLM services. The tokens are essentially never present in legitimate user input,
  so detection has near-zero false-positive rate.
  - Source: https://arxiv.org/abs/2510.10271
  - **aigis takeaway:** `jb_special_token_injection` pattern: detect <|...|> control tokens,
    [INST]/[/INST], <<SYS>>/<</SYS>> markers in user input. (**IMPLEMENTED**)

- **JBFuzz: Fuzzing-Based Automated Jailbreaking (arxiv:2503.08990, March 2026)**:
  Applies software fuzzing principles to LLM prompts: treats input space as a binary format
  to mutate, uses a lightweight seed corpus and an evaluator to evolve jailbreak payloads.
  Achieves 99% average ASR across GPT-4o, Gemini 2.0, and DeepSeek-V3 in ~7 queries and
  60 seconds. Requires only black-box API access. Signature mutations adapt to pattern matching,
  making it specifically effective against static rule-based defenses.
  - Source: https://arxiv.org/abs/2503.08990
  - **aigis takeaway:** JBFuzz adaptively mutates prompts to evade static patterns. The correct
    response is broader rule coverage (reducing the exploitable surface) plus rate-limit
    guidance. No single regex pattern addresses this; noted for future behavioral monitoring work.

- **Sockpuppeting — API Prefill Exploitation (Trend Micro / Dotsinski & Eustratiadis, 2026)**:
  Exploits assistant-role prefill support in LLM APIs: the attacker explicitly sets the last
  conversation message to role=assistant with "Sure, here's how to..." as content, causing the
  model to continue the fabricated response. Achieves 95% ASR on Qwen-8B and 77% on
  Llama-3.1-8B with zero optimization — a single-line attack. Affects 11 major models.
  - Source: https://www.trendmicro.com/vinfo/us/security/news/cybercrime-and-digital-threats/sockpuppeting-how-a-single-line-can-bypass-llm-safety-guardrails
  - **aigis takeaway:** Partially covered by `jb_affirmative_prefill` (DIA-I variant). The
    API-level variant (where the caller sets role=assistant) requires application-layer
    controls; the existing regex covers the prompt-injection variant where this is embedded
    in user text. No additional pattern needed this cycle.

- **Crescendo Multi-Turn Incremental Jailbreaking (arxiv:2404.01833, USENIX Security 2025)**:
  Incremental escalation following foot-in-the-door psychology: starts with innocuous context
  questions, then each response becomes the next prompt's foundation, gradually shifting toward
  restricted content. Up to 99.99% ASR with foundational context on LLaMA-2 70B; tested against
  GPT-4, Gemini-Pro, and Claude-3. A landmark multi-turn attack with high effectiveness.
  - Source: https://arxiv.org/abs/2404.01833
  - **aigis takeaway:** Requires stateful multi-turn trajectory analysis — out of scope for
    single-turn rule-based detection. Deferred; noted for future cross-session correlator work.

- **Persona/Roleplay Jailbreaks — RoleBreaker (arxiv:2507.22171, 2025)**:
  Automated framework for persona-based jailbreaks achieves 87.3% ASR on open-source models
  and 84.3% on commercial models. Uses Big Five personality framework and XML/JSON config
  mimicry (Policy Puppetry). Combined with temporal framing ("Time Bandit": set in a fictional
  era when policies didn't apply), achieves +10-20% over baseline roleplay.
  - Source: https://arxiv.org/abs/2507.22171
  - **aigis takeaway:** The baseline persona patterns (`jb_evil_roleplay`, `jb_no_restrictions`,
    `jb_hypothetical_ai`) cover most forms. Policy Puppetry (XML config injection) is partially
    overlapping with `jb_structured_extraction`. Time Bandit temporal framing is a gap — deferred
    to pending for next jailbreak-extraction cycle.

- **Many-Shot Variants: In-Context Poisoning at Scale (Anthropic, 2024, Persistent 2026)**:
  Context windows of 1M+ tokens enable 256+ demonstration shots. Effectiveness follows a power
  law; larger models are more vulnerable due to superior in-context learning. Prompt
  classification/modification reduced ASR from 61% to 2%.
  - Source: https://www.anthropic.com/research/many-shot-jailbreaking
  - **aigis takeaway:** `jb_many_shot` (score 55) already covers 3+ faux dialogue pairs.
    Extended many-shot at 256+ shots would require session-level context length monitoring
    rather than regex; no additional pattern this cycle.

---

## Candidate Hardenings

1. **`jb_poetry_harmful_framing`** (input, score 55) — Creative format directive (poem/rap/song)
   + harmful how-to or dangerous substance keyword within ~200 chars. **→ IMPLEMENTED**

2. **`jb_special_token_injection`** (input, score 70) — Control token injection:
   `<|...|>` tokens, `[INST]/[/INST]`, `<<SYS>>/<</SYS>>`. High confidence (near-zero
   false positives). **→ IMPLEMENTED**

3. *(pending)* Time Bandit temporal framing jailbreak (fictional era/date + harmful request).
   Well-defined but held back: pattern needs careful tuning to avoid false positives in
   legitimate historical-scenario questions.

4. *(pending)* JBFuzz adaptive mutation coverage — requires behavioral/rate-limit monitoring
   layer, not regex-based.

5. *(deferred from prior cycles)* Crescendo multi-turn incremental jailbreak — requires
   stateful session-level detection.
