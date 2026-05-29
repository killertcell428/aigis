# Research: jailbreak-extraction — 2026-05-29T06-00

## Domain: jailbreak-extraction (index 3, fourth pass)
## Cycle index: 3
## Cycle timestamp: 2026-05-29T06-00

Prior passes covered:
- Pass 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Pass 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Pass 3 (2026-05-13): Structured JSON/dict field enumeration, Extended sandwich attack with verbatim qualifiers.

This pass focuses on cipher/encoding response jailbreaks and payload splitting/step-enumerated decomposition attacks.

---

## Findings

- **CipherChat — Near-100% ASR via Cipher-Based Communication (arxiv:2308.06463, Yuan et al., 2023)**:
  The CipherChat framework demonstrated that instructing a model to communicate using a cipher scheme
  (SelfCipher, Caesar, ASCII, Morse, ROT13, Base64) bypasses safety alignment because safety training
  was conducted on natural language — not cipher-encoded text. On GPT-4, CipherChat achieved nearly
  100% attack success rate across 11 safety domains including violence, self-harm, misinformation,
  and illegal activities when the model was instructed to respond in cipher form. The input prompt
  assigns the model the role of a "cipher expert" and provides few-shot enciphered demonstrations,
  making the request appear as a cryptography task while the harmful instruction is encoded.
  - Source: https://arxiv.org/abs/2308.06463
  - **aigis takeaway:** Add `jb_cipher_response_request` pattern detecting inputs that ask the model
    to respond using cipher/encoding schemes. (**IMPLEMENTED**)

- **Jailbreaking LLMs Against Moderation Guardrails via Cipher Characters (arxiv:2405.20413, May 2024)**:
  Follow-up research confirmed that cipher character substitutions (using Unicode look-alikes and
  non-standard glyphs that resemble ASCII) can bypass production moderation APIs. The technique works
  because models trained on standard Unicode recognize the semantic meaning of cipher-substituted text
  while moderation systems only scan the raw byte-level representation. Success rates varied from 40%
  to 95% depending on the moderation provider and cipher complexity.
  - Source: https://arxiv.org/abs/2405.20413
  - **aigis takeaway:** Already partially covered by `enc_homoglyph_keyword` and related evasion
    patterns; the new `jb_cipher_response_request` pattern focuses on the explicit "respond in cipher"
    instruction, distinct from passive character substitution.

- **RoguePrompt — Dual-Layer Ciphering on Production Moderation Systems (arxiv:2511.18790, Nov 2025)**:
  RoguePrompt is an automated jailbreak pipeline that applies dual-layer ROT-13 + Vigenère transforms
  to forbidden prompts, wraps them in natural-language decoding instructions, and submits them to
  production-level moderation APIs. Evaluated against GPT-4o on 2,448 prompts previously marked as
  "strongly rejected" by a production moderation system, it achieved 93.93% filter bypass, 80.2%
  reconstruction, and 71.5% full execution success. The key mechanism: the model decodes the cipher
  from the natural-language instruction, then executes the hidden command, while the moderation scan
  only sees the cipher-encoded payload.
  - Source: https://arxiv.org/abs/2511.18790
  - **aigis takeaway:** This confirms the practical urgency of `jb_cipher_response_request`. The
    natural-language decoding instruction ("respond in ROT13 and then decode your reply...") is
    detectable at the input layer before the moderation system receives the obfuscated payload.
    (**Research basis for IMPLEMENTED pattern**)

- **"Novel Complex Ciphers" — Custom Encryption More Effective (arxiv:2402.10601, Feb 2024)**:
  Research by Handa et al. showed that novel user-defined ciphers (where the attacker invents a
  novel substitution or transposition rule and teaches it to the model in-context) are MORE effective
  than widely studied ciphers like ROT13 because defenses specifically targeting known ciphers don't
  cover custom schemes. ASR for novel ciphers reached 70-90% on models including GPT-3.5, GPT-4,
  and Claude-2 when the cipher was novel and the instruction was framed as a coding task.
  - Source: https://arxiv.org/abs/2402.10601
  - **aigis takeaway:** The `jb_cipher_response_request` pattern targets named ciphers; novel
    custom ciphers defined in-context are harder to detect via regex. This is a known limitation
    and a candidate for a future cycle (behavioral / semantic detection).

- **"Speak Easy" — Payload Splitting Raises GPT-4o ASR from 9.2% to 55.5% (ICML 2025, arxiv:2502.04322)**:
  Yong et al. demonstrated that decomposing a harmful request into multiple numbered sub-questions —
  each individually benign — substantially increases attack success rate. On the WildChat benchmark,
  GPT-4o's attack success rate rose from 9.2% baseline to 55.5% with payload splitting alone, and
  exceeded 90% when combined with multilingual translation. Each step passes individual content
  filters; the full sequence extracts the harmful information incrementally. The technique is
  distinct from Many-Shot jailbreaking (which fabricates dialogue turns) — it structures the query
  as a numbered tutorial or step list.
  - Source: https://arxiv.org/abs/2502.04322
  - **aigis takeaway:** Add `jb_payload_splitting` pattern detecting 3+ numbered steps combined
    with dangerous topic keywords. (**IMPLEMENTED from pending**)

- **MetaBreak — Special Token Manipulation (arxiv:2510.10271, Oct 2025)**:
  MetaBreak exploits how production LLM service APIs expose special tokens (system delimiters,
  turn-boundary tokens) through poorly sanitized API parameters. Injecting these tokens directly
  into the user message confuses the model into treating the user turn as a system instruction
  turn. MetaBreak outperforms prompt-engineering-only jailbreaks by 11.6% when no content
  moderation is deployed, and by 34.8% when standard moderation is applied. This is an
  infrastructure-level vulnerability, not a prompt-level one.
  - Source: https://arxiv.org/abs/2510.10271
  - **aigis takeaway:** Special token injection is partially covered by existing control-character
    and null-byte patterns. A dedicated `jb_special_token_injection` pattern looking for literal
    special token strings (`<|system|>`, `<|im_start|>`, `[INST]`, `[SYS]`) would improve
    coverage. Send to pending for next jailbreak-extraction cycle.

- **MetaCipher — Multi-Agent, Time-Persistent Cipher Attacks (arxiv:2506.22557, Jun 2025)**:
  MetaCipher introduces a multi-agent framework where an orchestrator LLM autonomously generates
  and rotates custom ciphers to evade detection, then instructs target LLMs to respond using those
  ciphers. The time-persistent aspect means the cipher scheme can be negotiated across sessions,
  making it harder for single-session filters to detect. This is beyond single-turn regex detection.
  - Source: https://arxiv.org/abs/2506.22557
  - **aigis takeaway:** Named cipher detection via `jb_cipher_response_request` addresses the
    known-cipher portion of this attack surface. Multi-session cipher negotiation requires
    cross-session behavioral analysis — roadmap item.

---

## Candidate Hardenings

1. **`jb_cipher_response_request`** (input, score 60) — Detects inputs asking the model to respond
   using named cipher/encoding schemes (ROT13, Caesar, Vigenère, pig Latin, Morse, base64).
   Research basis: CipherChat (arxiv:2308.06463, ~100% ASR) and RoguePrompt (arxiv:2511.18790,
   93.93% bypass). **→ IMPLEMENTED**

2. **`jb_payload_splitting`** (input, score 45) — Detects 3+ numbered-step decomposition of harmful
   requests. Research basis: "Speak Easy" (ICML 2025, arxiv:2502.04322, 55.5% ASR).
   **→ IMPLEMENTED (from pending)**

3. *(pending)* Special token injection (`jb_special_token_injection`) — Detecting literal special
   tokens (`<|system|>`, `[INST]`, etc.) in user messages. MetaBreak (arxiv:2510.10271).
   Infrastructure-level; needs careful false-positive analysis for technical users.

4. *(pending)* Novel custom cipher detection — Requires semantic/behavioral analysis, not regex.
   MetaCipher (arxiv:2506.22557).
