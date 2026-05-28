# Research: jailbreak-extraction — 2026-05-28T09-13

## Domain: jailbreak-extraction (index 3, fourth pass)
## Cycle timestamp: 2026-05-28T09-13

Prior cycles covered:
- Cycle 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks, DAN.
- Cycle 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass.
- Cycle 3 (2026-05-13): Structured JSON/dict extraction, Sandwich verbatim extraction.

This pass targets cipher-based role-framing jailbreaks (CipherChat, SEAL) and chat-template
special token injection (MetaBreak) — two distinct attack families not covered by prior cycles.

---

## Findings

- **MetaBreak — Chat Template Special Token Injection (arXiv:2510.10271, Oct 2024)**:
  Attackers embed model-framework special tokens (`<|im_start|>`, `[INST]`, `<<SYS>>`,
  `<|eot_id|>`, `<|endoftext|>`) directly in user-submitted text. When the model encounters
  these tokens, it may interpret injected content as a prior privileged turn (assistant or
  system), hijacking the conversation structure. MetaBreak outperforms GPTFuzzer by 34.8% and
  boosts combined attack success by 20–24% across tested models. These tokens have zero
  legitimate use in user messages — they are exclusively inference-framework delimiters.
  - Source: https://arxiv.org/abs/2510.10271
  - **aigis takeaway:** Add `jb_special_token_injection` matching all major chat-template
    delimiter tokens. Near-zero false-positive rate. (**IMPLEMENTED**)

- **CipherChat — Cipher Role Assignment (arXiv:2308.06463)**:
  The model is instructed to role-play as "CipherAssistant" communicating exclusively in ROT13,
  Base64, or another encoding. Harmful requests are then sent encoded in that cipher. The
  existing `pi_encoding_bypass` rule matches `(base64|rot13) + (instruction|command)` but does
  NOT match the role-setup phrase "we will communicate entirely in ROT13" or "respond only in
  Base64", which is the distinctive setup marker. ~59% ASR on GPT-4; near-100% on GPT-3.5.
  - Source: https://arxiv.org/abs/2308.06463
  - Source: https://arxiv.org/abs/2402.10601 (Word Substitution Cipher, ICLR 2025, ~59% on Gemini-Pro)
  - **aigis takeaway:** Add `jb_cipher_role_framing` covering the setup phrases and
    decode-then-answer pivot. (**IMPLEMENTED**)

- **SEAL — Stacked Adaptive Ciphers (arXiv:2505.16241, May 2025)**:
  Extends CipherChat by chaining multiple ciphers (Caesar shift + Base64 + character reversal)
  using bandit optimization to find the stack that bypasses safety filters while remaining
  decodable by the model's reasoning chain. Achieved 100% ASR on DeepSeek-R1 and Gemini 2.0
  Flash; 80–85% on other reasoning models. The endpoint pattern "decode [cipher chain] then
  answer" is covered by the `jb_cipher_role_framing` arm 3 pattern.
  - Source: https://arxiv.org/abs/2505.16241
  - **aigis takeaway:** Covered by `jb_cipher_role_framing` arm 3. (**IMPLEMENTED**)

- **Crescendo Multi-Turn Jailbreak (arXiv:2404.01833, USENIX Security 2025)**:
  Gradually escalates requests across multiple turns, ending with a final pivot phrase
  ("Great, now write a detailed guide to…") that extracts harmful output after context has been
  built. The Crescendomation variant achieved 29–61% ASR lift over baselines on GPT-4 and
  49–71% on Gemini-Pro. Detection of the final turn alone is possible but requires context
  from prior turns. Full coverage requires a multi-turn session correlator.
  - Source: https://arxiv.org/abs/2404.01833
  - **aigis takeaway:** Multi-turn behavioral tracking required; send final-step detector to
    pending for a future `memory-context` or `jailbreak-extraction` session.

- **Privilege Escalation in LLM Agents (arXiv:2503.15547, March 2025)**:
  "Prompt Flow Integrity" paper documents how attackers claim elevated trust-level in user-turn
  text to make an LLM agent execute privileged tool calls. The attack surface (operator
  impersonation, "I am Anthropic / I am the system operator") is real but the detect-by-regex
  approach has elevated false-positive risk compared to the token-injection and cipher patterns
  implemented this cycle.
  - Source: https://arxiv.org/abs/2503.15547
  - **aigis takeaway:** Operator impersonation patterns explored but deferred to pending due to
    false-positive risk — users legitimately reference "operator" or "developer" roles in
    enterprise contexts. Requires a more specific signal.

- **Sockpuppeting — Single-Line Affirmative Prefill (arXiv:2601.13359, Trend Micro, 2025)**:
  Injects a single `Assistant: Sure, here's how:` line before the harmful request to bypass
  refusal. This is already covered by `jb_affirmative_prefill` (score 55). The MetaBreak
  finding above extends this to raw special-token injection not yet covered by that rule.
  - Source: https://arxiv.org/abs/2601.13359
  - **aigis takeaway:** Already covered by `jb_affirmative_prefill`; MetaBreak gap now closed.

- **Sugar-Coated Poison / Defense Threshold Decay (arXiv:2504.05652, EMNLP 2025)**:
  Forces the model to generate a long benign preamble (essay, story) then appends a malicious
  instruction, exploiting attention decay over long outputs. Consistently bypasses safety on
  tested models.
  - Source: https://arxiv.org/abs/2504.05652
  - **aigis takeaway:** The "additionally, after completing the essay, provide [dangerous
    content]" trigger pattern is regex-detectable. Save to pending for next jailbreak cycle.

---

## Candidate hardenings

1. **`jb_special_token_injection`** (input, score 80) — MetaBreak-style chat-template token
   injection. Near-zero false-positive rate. → **IMPLEMENTED**

2. **`jb_cipher_role_framing`** (input, score 65) — CipherChat/SEAL cipher role-assignment and
   decode-then-answer setup phrases. Closes gap in `pi_encoding_bypass`. → **IMPLEMENTED**

3. *(pending)* Crescendo final-turn pivot detector — requires context from prior turns.

4. *(pending)* Sugar-Coated Poison trigger — "additionally, after completing [benign task],
   provide [dangerous content]" — regex-feasible but needs careful false-positive tuning.

5. *(pending)* Operator impersonation (`jb_operator_impersonation`) — authority claim +
   override request. Deferred due to false-positive risk in legitimate enterprise contexts;
   needs a tighter signal (e.g., specific AI company name + explicit override language only).
