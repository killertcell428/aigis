# Research: jailbreak-extraction — 2026-05-31T00-12

## Domain: jailbreak-extraction (index 3, fourth pass)
## Cycle timestamp: 2026-05-31T00-12

Prior cycles covered:
- Pass 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Pass 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Pass 3 (2026-05-13): Structured JSON extraction, Sandwich attack, Autonomous LLM-vs-LLM jailbreaking.

This pass focuses on:
- Adversarial poetry / creative-format jailbreaks (pending since pass 2)
- Payload splitting / step-enumerated decomposition (pending since pass 2)
- RoguePrompt dual-layer ciphering (new)
- Persona-prompt enhancement attacks (new)

---

## Findings

- **Adversarial Poetry as a Universal Single-Turn Jailbreak** (arxiv:2511.15304, Nov 2025):
  Encoding harmful requests in poetic form (ballad, rap, rhyme, haiku, verse) achieves 62% ASR
  for hand-crafted poems and 43% for automated meta-prompt conversions across 25 frontier models
  including GPT-4o, Gemini 2.5, and Claude 3.7. Some providers exceeded 90% ASR in specific risk
  categories (cyber-offense: 84%). The meta-prompt approach converted 1,200 ML-Commons harmful
  prompts into verse with ASRs up to 18× higher than prose baselines. The mechanism is stylistic
  obfuscation: the model prioritizes adherence to the poetic form constraint over safety alignment.
  - Source: https://arxiv.org/abs/2511.15304
  - **aigis takeaway:** A (write/compose/create) + (poem/rap/ballad/…) directive co-occurring with
    a dangerous how-to keyword within ~200 chars is detectable as a single-turn pattern.
    The `jb_poetry_harmful_framing` pending item (2026-05-10) is ready to implement.

- **Payload Splitting / Step-Enumerated Decomposition (Speak Easy, ICML 2025, arxiv:2502.04322)**:
  Decomposes a harmful request into multiple numbered innocuous sub-queries where the dangerous
  topic only surfaces in later steps. GPT-4o ASR increases from 0.092 to 0.555; combined with
  TAP-T, exceeds 0.90. A single-message variant embeds all steps in one prompt. No single step
  triggers a naive content filter because each appears benign in isolation.
  - Source: https://arxiv.org/abs/2502.04322
  - **aigis takeaway:** A numbered-step structure (step 1/2/3) where a dangerous keyword appears
    in step 3+ is detectable in single-message form. The `jb_payload_splitting` pending item
    (2026-05-10) is ready to implement.

- **RoguePrompt: Dual-Layer Ciphering for Self-Reconstruction** (arxiv:2511.18790, Nov 2025):
  Uses two sequential encoding layers (ROT-13 + Vigenère) with embedded natural-language
  decoding instructions in a single query. Evaluated on 313 real-world hard-rejected prompts
  across multiple frontier LLMs: 93.93% filter bypass rate, 79.02% instruction reconstruction,
  70.18% execution success rate. The encoded payload is unrecognizable to surface regex scanners.
  - Source: https://arxiv.org/abs/2511.18790
  - **aigis takeaway:** Two-layer ciphers with embedded decoding instructions are detectable via
    pattern matching (ROT-13 trigger phrase + "decode" instruction). However, the detection
    surface is narrow and false-positive risk is higher than for other patterns. Deferred to
    pending until a robust formulation is identified.

- **Persona-Prompt Jailbreak Enhancement** (arxiv:2507.22171, Jul 2025): A genetic algorithm
  automatically crafts persona prompts that reduce LLM refusal rates by 50–70% across multiple
  models. These prompts work synergistically with existing jailbreak methods, increasing their
  success by 10–20%. The persona (e.g., "You are a helpful assistant") is placed in user input
  rather than the system prompt. This paper maps to the existing `jb_evil_roleplay` and
  `jb_hypothetical_ai` patterns — no new single-turn pattern is unique enough to warrant a
  separate rule.
  - Source: https://arxiv.org/abs/2507.22171
  - **aigis takeaway:** The existing persona-override patterns provide reasonable coverage.
    No new pattern this cycle.

- **Bypassing LLM Guardrails via Character Injection (arxiv:2504.11168, Apr 2025)**:
  Demonstrates evasion of six commercial guardrail systems (including Azure Prompt Shield and
  Meta Prompt Guard) via whitespace injection, leetspeak substitution, and word importance
  ranking. Achieves up to 100% evasion against specific systems while "maintaining adversarial
  utility." The evasion is in the encoding layer, not the semantic layer — the underlying
  jailbreak intent is unchanged.
  - Source: https://arxiv.org/abs/2504.11168
  - **aigis takeaway:** aigis rule-based patterns are also vulnerable to encoding evasion, but
    the `evasion-obfuscation` domain (index 7) is the right place to address this systematically.
    No new pattern here.

- **Web-Scale Indirect Injection Spreading (Google Threat Intelligence, Apr 2026)**:
  Google's threat team confirmed that open web content is being seeded with prompt-injection
  payloads targeting AI agents browsing the web. The malicious-category share of indexed pages
  rose 32% in three months. Sean Park (OWASP [un]prompted 2026) demonstrated a KYC pipeline
  exploit where a passport image contained instructions in hidden OCR text.
  - Source: https://medium.com/@Micheal-Lanham/indirect-prompt-injection-at-scale-2643e089fe3a
  - **aigis takeaway:** Covered by the `prompt-injection` domain (index 0). No new
    jailbreak-extraction pattern.

---

## Candidate Hardenings

1. **`jb_poetry_harmful_framing`** (input, score 55) — Poetry/rap/ballad/song directive
   co-occurring with a dangerous how-to keyword within ~200 chars. Implements the pending item
   from 2026-05-10. **→ IMPLEMENT THIS CYCLE**

2. **`jb_payload_splitting`** (input, score 45) — Numbered step-structure where a dangerous
   keyword appears in step 3+. Implements the pending item from 2026-05-10.
   **→ IMPLEMENT THIS CYCLE**

3. *(deferred)* RoguePrompt dual-layer cipher detection — ROT-13/Vigenère embedded decoding
   instructions. Narrow detection surface, higher false-positive risk. Save to pending.

4. *(already covered)* Persona-prompt enhancement — covered by existing jailbreak patterns.

5. *(other domain)* Web-scale indirect injection — covered by `prompt-injection` domain.
