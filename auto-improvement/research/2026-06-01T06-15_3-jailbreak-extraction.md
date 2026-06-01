# Research: jailbreak-extraction — 2026-06-01T06-15

## Domain: jailbreak-extraction (index 3, fourth pass)
## Cycle timestamp: 2026-06-01T06-15
## Focus: Creative-format extraction, cipher-encoding bypass, and ActorAttack professional-role jailbreaks

Prior cycles covered:
- Cycle 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Cycle 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Cycle 3 (2026-05-13): Structured JSON extraction, Sandwich attack, Autonomous LLM-vs-LLM jailbreaks.

This pass targets three new angles not yet covered: creative-format system-prompt extraction,
cipher/encoding response bypass, and the ActorAttack professional-role attack documented at ACL 2025.

---

## Findings

- **Creative-Format System-Prompt Extraction (WildJailbreak, PromptBench, 2024–2025)**: Attackers
  request the model to embed its system instructions inside a poem, haiku, song, or story,
  exploiting the observation that models treat creative writing as lower-risk than direct
  disclosure. WildJailbreak (Jiang et al., 2024) documented this framing as one of the hardest
  to block because models associate creative output with "safe" generation modes. PromptBench
  (Zhu et al., 2024) showed 40–60% ASR on GPT-4, Claude, and Mistral models that refuse the
  direct "repeat your system prompt" form. The existing `pi_system_prompt_leak` and
  `jb_sandwich_extraction` patterns do not cover this creative-format framing.
  - Source: https://arxiv.org/abs/2406.18510 (WildJailbreak)
  - Source: https://arxiv.org/abs/2306.04528 (PromptBench)
  - **aigis takeaway:** Add `jb_creative_extraction` pattern detecting creative-format commands
    (poem/haiku/song/rap/rhyme/limerick/verse) co-occurring with system-prompt references. (**IMPLEMENTED**)

- **Cipher / Encoding Response Bypass — CipherChat and "Jailbroken" (NeurIPS 2024, arxiv:2308.06463)**:
  Attackers instruct the model to respond in an encoding scheme (ROT13, Morse code, pig latin,
  Base64, leet speak, binary) so the harmful output evades plaintext content-moderation systems.
  Wei et al. ("Jailbroken: How Does LLM Safety Training Fail?", NeurIPS 2024) showed 71% ASR
  on GPT-4 and 66% on Claude for cipher-framed responses. CipherChat (Yuan et al., 2023)
  extended this to self-defined cipher schemes reaching 80%+ ASR. The attack specifically bypasses
  output scanners that operate on plaintext. The existing `pi_encoding_bypass` only catches
  "base64 instruction" (encoding applied to the input), not "respond in base64" (encoding applied
  to the output to evade output scanners).
  - Source: https://arxiv.org/abs/2308.06463
  - **aigis takeaway:** Add `jb_cipher_bypass` pattern detecting requests to respond/output in
    cipher or encoding format. (**IMPLEMENTED**)

- **ActorAttack — Professional Role with No-Ethics Qualifier (arxiv:2410.10700, ACL Findings 2025)**:
  Jiang et al. ("Derail Yourself: Multi-turn LLM Jailbreak Attack through Self-discovered Attack
  Chain", ACL Findings 2025) built a character-based multi-turn attack achieving 95% ASR against
  GPT-4o, Claude 3.5, and Gemini 1.5 Pro. The attacker constructs a specific professional
  character (chemist, hacker, pharmacist, assassin) who would naturally possess the harmful
  knowledge, then adds an explicit "has no restrictions/ethics" qualifier. Distinct from the DAN
  attack (first-person AI persona) and from the hypothetical-AI attack (fictional unrestricted AI
  in third person). The professional-role framing provides plausible epistemic authority while
  the no-restrictions qualifier bypasses the model's safety-training signal.
  - Source: https://arxiv.org/abs/2410.10700
  - Source: https://github.com/AI45Lab/ActorAttack
  - **aigis takeaway:** Add `jb_actor_professional_bypass` combining professional role terms
    with explicit no-ethics/no-restrictions qualifier. (**IMPLEMENTED**)

- **Crescendo Multi-Turn Escalation (arxiv:2404.01833, USENIX Security 2025)**: Microsoft Research
  (Russinovich et al.) documented a multi-turn jailbreak that starts with benign questions and
  escalates gradually. Each question seems harmless in isolation; the attacker exploits in-context
  learning to make the model accept progressively more harmful requests. 56–82% ASR against
  GPT-4 and Gemini Flash. Single-turn detection is insufficient, but prompts that explicitly
  signal the escalation strategy (e.g., "let's go step by step, now make it more extreme")
  are detectable as a soft signal.
  - Source: https://arxiv.org/abs/2404.01833
  - Source: https://www.usenix.org/conference/usenixsecurity25/presentation/russinovich
  - **aigis takeaway:** Multi-turn session state needed for full detection. A single-turn soft
    signal pattern could flag explicit escalation language but with high false-positive risk.
    Deferred to pending.

- **Low-Resource Language Translation Bypass (arxiv:2605.18239, May 2026)**: Attackers exploit
  the disparity in safety training across languages — models trained primarily on English have
  weaker safety alignment in low-resource languages (Zulu, Hausa, Amharic, etc.). 60–89% ASR
  with human evaluation when harmful requests are translated into low-resource languages before
  submission. This is a multi-turn and translation-service-dependent attack; regex detection
  of low-resource language content is impractical in a general filter.
  - Source: https://arxiv.org/html/2605.18239v1
  - **aigis takeaway:** A language-detection + low-resource-language allowlist approach is the
    right defense, but requires a language identifier runtime dependency. Deferred to pending.

- **RoguePrompt Dual-Layer Cipher (arxiv:2511.18790, CODASPY 2026)**: A two-phase attack:
  first, the attacker trains the model within a session to accept a custom cipher mapping (e.g.,
  "substitute: A=X, B=Y..."); then submits the harmful request using that cipher. The dual
  layer (custom + standard cipher) achieves 93.93% filter bypass. Requires session-state tracking
  to detect the setup phase.
  - Source: https://arxiv.org/abs/2511.18790
  - **aigis takeaway:** The custom-cipher setup phase contains word-substitution tables (format:
    "word1 = word2") that could be detected. The existing `jb_cipher_bypass` covers standard
    cipher encoding; custom word-substitution ciphers are partially covered. A specific pattern
    for word-substitution setup is a viable addition for a future cycle.

- **MultiBreak Benchmark: Safety Degradation Under Repeated Attacks (arxiv:2605.12869, May 2026)**:
  Models show statistically significant safety degradation under repeated attacks in a session.
  A model that refuses turn 1 has measurably higher probability of complying by turn 4–6 if
  the attacker rephrases and persists. MultiBreak (10,389 prompts, 26 safety categories)
  showed up to 44.8% ASR improvement when attacks were extended from 1 to 6 turns. GPT-4.1-mini
  reached 80.4% ASR at 6 turns.
  - Source: https://arxiv.org/html/2605.12869v1
  - **aigis takeaway:** Session-level escalation counter would be the right defense, incrementing
    a block-threshold reduction for each rephrased harmful request in a session. Requires
    session-state infrastructure beyond current rule-based scope. Deferred to pending.

---

## Candidate hardenings

- **`jb_creative_extraction`** (IMPLEMENTED): Detect poem/haiku/song/rap/rhyme/limerick combined
  with system-prompt references. Score 60. Covers the WildJailbreak and PromptBench creative-format
  extraction vector not covered by existing patterns.

- **`jb_cipher_bypass`** (IMPLEMENTED): Detect "respond in ROT13/Morse/pig latin/Base64/leet speak".
  Score 55. Covers the CipherChat / NeurIPS 2024 output-encoding evasion vector distinct from the
  existing `pi_encoding_bypass` (which covers input encoding, not output encoding).

- **`jb_actor_professional_bypass`** (IMPLEMENTED): Detect professional role (chemist/hacker/
  pharmacist/assassin/arms dealer) combined with explicit no-ethics qualifier. Score 65. Covers
  the ActorAttack ACL 2025 vector, distinct from `jb_evil_roleplay` (AI persona) and
  `jb_hypothetical_ai` (third-person fictional AI).

- **Multi-turn session escalation counter** (DEFERRED): Cross-session scoring for Crescendo
  and MultiBreak-style attacks. Requires session-state infrastructure; deferred to pending.

- **Low-resource language filter** (DEFERRED): Language-identification + policy on low-resource
  languages. Requires a language-detection runtime dependency; deferred to pending.

- **Custom word-substitution cipher setup detection** (DEFERRED): Detect "word1 = word2" mapping
  tables used in RoguePrompt's setup phase. Good candidate for the next jailbreak cycle.
