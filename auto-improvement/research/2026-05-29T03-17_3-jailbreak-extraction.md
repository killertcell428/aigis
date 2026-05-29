# Research: jailbreak-extraction — 2026-05-29T03-17

## Domain: jailbreak-extraction (index 3, fourth pass)
## Cycle timestamp: 2026-05-29T03-17
## Focus: Language-based and encoding-based extraction bypass techniques; sockpuppetting; reasoning-model attacks

Prior cycle coverage for this domain:
- Cycle 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Cycle 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Cycle 3 (2026-05-13): Structured JSON/Dict extraction, Extended sandwich attack (verbatim qualifier).

This pass targets: translation-based extraction bypasses, encoding-based extraction bypasses, sockpuppetting (output-prefix injection), and reasoning-model disruption attacks.

---

## Findings

- **Translation-Based System-Prompt Extraction (DecipherGuard, arxiv:2509.16870, Sep 2025)**:
  Attackers bypass keyword-based detectors that look for "show me your system prompt" by instead
  requesting the model to translate its system prompt into a foreign language (French, Spanish,
  Chinese, etc.). The model sees this as a benign translation task and often complies. DecipherGuard
  empirically documented this as a primary extraction channel alongside base64 encoding, achieving
  guardrail evasion because most filters only match English-language extraction vocabulary. The
  Adversarial Prompt Translation study (arxiv:2410.11317, Oct 2024) further demonstrated 81.8% ASR
  against seven commercial LLMs using multilingual obfuscation.
  - Source: https://arxiv.org/abs/2509.16870
  - Source: https://arxiv.org/abs/2410.11317
  - **aigis takeaway:** Add `jb_translation_extraction` covering translation + system-prompt
    reference + target language. (**IMPLEMENTED**)

- **Encoded-Output System-Prompt Extraction (DecipherGuard, arxiv:2509.16870, Sep 2025)**:
  Attackers ask the model to return its system prompt encoded in base64, hex, or rot13, bypassing
  output-side scanners that check for literal system-prompt text. The encoded output is meaningless
  to naive output filters but trivially decoded by the attacker. DecipherGuard confirmed that
  guardrail systems misclassify base64-encoded extraction requests at significantly higher rates
  than plaintext requests. This is distinct from `enc_base64_instruction` (which catches
  base64-encoded *inputs*) and `jb_structured_extraction` (JSON/dict field enumerations).
  - Source: https://arxiv.org/abs/2509.16870
  - **aigis takeaway:** Add `jb_encoded_extraction` covering base64/hex/rot13 + system-prompt
    extraction language. (**IMPLEMENTED**)

- **Sockpuppetting: Output-Prefix Injection (arxiv:2601.13359, Jan 2026)**:
  A hybrid jailbreak injects adversarial content into the *assistant* message block of open-weight
  LLM chat templates, rather than the user prompt, achieving 22–99% ASR across Gemma-7B, Llama-3.1-8B,
  and Qwen3-8B. The attack uses gradient-optimized suffixes placed inside the assistant turn to
  force harmful continuations. The existing `jb_affirmative_prefill` (score 65) covers the
  user-input variant of dialogue injection; sockpuppetting is a lower-level template manipulation
  requiring API-level access — regex-detectable only at the chat-completion API format level.
  - Source: https://arxiv.org/abs/2601.13359
  - **aigis takeaway:** The `jb_affirmative_prefill` pattern covers the user-prompt-side
    sockpuppetting variant. Full sockpuppetting at the API/template level requires schema-level
    validation of chat message roles, not text-level regex. Send to pending for a chat-template
    role validator.

- **Multi-Stream Perturbation Attack (arxiv:2603.10091, Mar 2026)**:
  Exploits "thinking mode" LLMs (Qwen3, DeepSeek, Gemini 2.5 Flash) by interleaving multiple
  competing task streams in a single prompt, disrupting chain-of-thought reasoning. Achieves
  thinking collapse rates up to 17% and response repetition up to 60%, with safety bypasses via
  reasoning disruption. Targets the CoT layer, not the text layer — no text pattern is specific
  enough for low-false-positive regex detection.
  - Source: https://arxiv.org/abs/2603.10091
  - **aigis takeaway:** Behavioral/reasoning-layer attack; regex detection insufficient in
    single-turn mode. Send to pending for a multi-task interleaving heuristic guide.

- **Bypass of LLM Guardrail Systems via Character Injection (arxiv:2504.11168, Apr 2025)**:
  Tested against Microsoft Azure Prompt Shield, Meta Prompt Guard, and four others. Character
  injection (inserting zero-width spaces, soft hyphens, invisible Unicode) and AML perturbation
  achieve up to 100% evasion against classifier-based guards. aigis rule-based scanner is less
  susceptible than ML classifiers to many of these since regex operates on the raw character
  sequence, but zero-width characters can split rule tokens. The existing `enc_unicode_control`
  and `evasion_zero_width` patterns cover this at the evasion-obfuscation layer.
  - Source: https://arxiv.org/abs/2504.11168
  - **aigis takeaway:** Largely covered by existing obfuscation patterns. No new rule needed.

- **Jailbroken Frontier Models Retain Capabilities (arxiv:2605.00267, May 2026)**:
  Study of 28 jailbreak methods across 5 benchmarks shows that frontier models (Claude Opus 4.6,
  GPT-4o) retain 92–96% of capability after jailbreaking, with Boundary Point Jailbreaking
  achieving "near-perfect classifier evasion with near-zero degradation." Smaller models lose more
  (Claude Haiku 4.5: 33.1% degradation). Confirms the arms-race nature of the field and that
  capability degradation is not a reliable safety signal.
  - Source: https://arxiv.org/abs/2605.00267
  - **aigis takeaway:** Confirms that comprehensive rule coverage reducing the attack surface
    is the right approach for a rule-based firewall. No specific new rule; informs the overall
    strategy of adding layered extraction pattern coverage.

- **Reasoning Hijacking for LLM Agents (arxiv:2604.05549, Apr 2026)**:
  JailAgent framework avoids modifying user prompts and instead implicitly manipulates agent
  memory and reasoning trajectory via "Trigger Extraction, Reasoning Hijacking, and Constraint
  Tightening." Achieves strong cross-model results but requires multi-turn agent interaction and
  memory access — not detectable by single-turn text scanning.
  - Source: https://arxiv.org/abs/2604.05549
  - **aigis takeaway:** Multi-turn, memory-layer attack. No regex rule applicable in the current
    single-turn filter architecture. Send to pending.

---

## Candidate Hardenings

1. **`jb_translation_extraction`** (input, score 60) — Translation + system-prompt reference +
   target language. **→ IMPLEMENTED**

2. **`jb_encoded_extraction`** (input, score 65) — Encoded output request (base64/hex/rot13)
   combined with system-prompt access language. **→ IMPLEMENTED**

3. *(pending)* Sockpuppetting chat-template role validator — validate that chat-completion
   requests do not contain assistant-role turns with adversarial optimization patterns; requires
   API-level schema validation, not regex.

4. *(pending)* Multi-stream perturbation heuristic — detecting concurrent interleaved task
   streams targeting reasoning-mode LLMs; requires multi-task parsing, not single regex.

5. *(pending)* JailAgent / reasoning hijacking detection — multi-turn, memory-layer; requires
   session-level state tracking beyond current architecture.
