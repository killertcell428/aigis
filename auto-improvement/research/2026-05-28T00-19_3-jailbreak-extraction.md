# Research: jailbreak-extraction — 2026-05-28T00-19

## Domain: jailbreak-extraction (index 3, fourth pass)
## Cycle timestamp: 2026-05-28T00-19

Prior cycles covered:
- Cycle 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Cycle 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Cycle 3 (2026-05-13): Structured JSON extraction, sandwich verbatim extraction.

This pass targets cipher/encoding-based jailbreaks and multi-turn payload-splitting
attacks, with a focus on single-turn detectable signals.

---

## Findings

- **RoguePrompt: Dual-Layer Cipher Jailbreak (arXiv:2511.18790, Nov 2025, CODASPY '26)**:
  RoguePrompt applies two nested encodings (ROT-13 + Vigenère cipher) and embeds natural-language
  decoding instructions, producing a prompt that looks benign to static content filters while
  instructing the model to decode and execute the harmful payload. Evaluated against GPT-4o on
  2,448 prompts previously rejected by production moderation: achieved 84.7% bypass rate,
  80.2% reconstruction rate, 71.5% full execution rate. Average across multiple LLMs: 93.93%
  filter bypass. The attack succeeds because the content filter sees only encoded text and
  decoding instructions, while the LLM's reasoning capability reconstructs and acts on the
  original intent.
  - Source: https://arxiv.org/abs/2511.18790
  - **aigis takeaway:** Add `jb_cipher_output_evasion` pattern: when an AI is asked to *respond*
    in a specific cipher/encoding AND the prompt references a safety filter or monitor, this is
    a high-confidence evasion attempt.

- **ACE/LACE: Custom Cipher Jailbreaks via LLM Reasoning (arXiv:2402.10601, published ICLR 2025)**:
  As safety fine-tuning has learned to detect Base64 and ROT-13 encoded malicious prompts,
  attackers now use novel user-defined ciphers (Caesar variant, custom substitution, word-level
  encoding). ACE (Attacks using Custom Encryptions) and LACE (Layered Attacks using Custom
  Encryptions) exploit the fact that advanced reasoning models can interpret complex ciphers
  without training exposure. Against GPT-4o, Caesar-variant ACE achieved 67% ASR. LACE
  stacks 2–3 cipher layers to further defeat pattern detection.
  - Source: https://arxiv.org/abs/2402.10601
  - **aigis takeaway:** Add `jb_decode_and_follow` pattern: "decode [cipher] and follow/act on
    the instructions" is a specific, detectable signal distinguishable from legitimate cipher
    discussions.

- **Jigsaw Puzzles (JSP) Multi-Turn Payload Splitting (arXiv:2410.11459, Oct 2024)**:
  JSP splits a harmful question into harmless fragments across multiple turns, then instructs
  the model to "reassemble" the question and answer it. Achieved 93.76% average ASR across five
  frontier LLMs (Gemini-1.5-Pro, Llama-3.1-70B, GPT-4, GPT-4o, GPT-4o-mini) and 92% on GPT-4
  alone. The single-turn variant explicitly asks the model to combine supplied parts: e.g.,
  "Part 1: [harmless]. Part 2: [harmless]. Now combine and answer." This is detectable in
  single-pass filters.
  - Source: https://arxiv.org/abs/2410.11459
  - **aigis takeaway:** Candidate for `jb_payload_split_reassemble` (pending — the single-turn
    signal is hard to reliably distinguish from legitimate "combine these pieces" requests).

- **Foot-in-the-Door (FITD) Multi-Turn Jailbreak (arXiv:2502.19820, Feb 2025)**:
  FITD progressively escalates malicious intent across turns via "bridge prompts" — each turn
  builds on the model's previous output. Achieved 94% average ASR across 7 models, including
  GPT-4o, Gemini-1.5-Pro, and Claude 3.5 Sonnet. Key distinguishing feature: early turns are
  genuinely benign; only the final turn contains the harmful request leveraging the established
  context. This is a multi-turn behavioral attack — not detectable in single-turn input filters
  but detectable in cross-session behavioral monitors.
  - Source: https://arxiv.org/abs/2502.19820
  - **aigis takeaway:** Not directly implementable as a single-turn regex. Send to pending for
    future cross-session escalation monitoring.

- **Crescendo: Multi-Turn Gradual Escalation (arXiv:2404.01833, USENIX Security 2025)**:
  Microsoft Research study formalizing the "foot-in-the-door" attack on LLMs. CrescendoMation
  (the automated variant) outperforms state-of-the-art jailbreaks by 29–61% on GPT-4 and
  49–71% on Gemini-Pro. Key observation: each individual turn is benign; the attack relies on
  accumulated conversational context. A secondary single-turn signal exists when the attacker
  explicitly references a prior established context: "Now that we've established [benign topic],
  explain how to [harmful escalation]." This escalation framing is rare in benign prompts.
  - Source: https://arxiv.org/abs/2404.01833; https://www.usenix.org/conference/usenixsecurity25/presentation/russinovich
  - **aigis takeaway:** "Now that we've established / agreed / discussed [X], [harmful
    escalation]" could be a Crescendo escalation signal. Send to pending — false positive risk
    is moderate in single-turn context.

- **Analysis of LLMs Against Prompt Injection and Jailbreak Attacks (arXiv:2602.22242, Feb 2026)**:
  Large-scale evaluation across Phi, Mistral, DeepSeek-R1, Llama 3.2, Qwen, and Gemma variants
  found that defense mechanisms operating as input filters are consistently bypassed by long,
  reasoning-heavy prompts. A key vulnerability: when jailbreak instructions are embedded inside
  chain-of-thought framing ("Step 1: reason about X. Step 2: ..."), safety training is less
  effective than direct prompts. Also found that encoder-decoder architectures (BERT-family)
  show stronger inherent resilience to jailbreaks than decoder-only LLMs.
  - Source: https://arxiv.org/abs/2602.22242
  - **aigis takeaway:** Reinforces value of rule-based input filters as a complementary layer to
    model-level safety. No specific new rule, but confirms the cipher-evasion and decode-and-
    follow patterns are worth implementing.

- **The Promptware Kill Chain (arXiv:2601.09625, Jan 2026)**:
  Documents how promptware (LLM-native malware) evolved to include native command-and-control
  using multi-step encoded instructions. Ciphered payloads appear in 17% of documented
  promptware samples from 2025–2026. The paper defines a kill-chain model with phases:
  injection → persistence → command execution, paralleling traditional malware.
  - Source: https://arxiv.org/pdf/2601.09625
  - **aigis takeaway:** Confirms that cipher-encoded instructions are a real operational pattern
    in LLM-targeting malware (promptware), not just academic PoCs.

---

## Candidate Hardenings

1. **`jb_cipher_output_evasion`** (input, score 50) — Detect requests asking the AI to respond
   in a cipher/encoding specifically to evade the content monitor or safety filter.
   **→ IMPLEMENTING THIS CYCLE**

2. **`jb_decode_and_follow`** (input, score 60) — Detect requests to decode a non-standard
   cipher and act on / follow the decoded instructions. Complements `pi_base64_payload` (which
   only covers `base64 + execute/run/eval`) by covering broader cipher types and "follow/obey"
   action verbs.
   **→ IMPLEMENTING THIS CYCLE**

3. *(pending)* `jb_payload_split_reassemble` — Single-turn variant of JSP: "Part 1: [harmless].
   Part 2: [harmless]. Combine and answer." False positive risk: high (legitimate
   multi-part questions use this framing). Needs a more specific signal.

4. *(pending)* Crescendo escalation framing — "Now that we've established [X], explain how to
   [harmful]." Multi-turn behavioral detection is more appropriate; single-turn signal has
   moderate false positive risk.

5. *(pending)* FITD multi-turn behavioral escalation — Requires cross-session correlation;
   regex-only rule is insufficient.
