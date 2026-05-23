# Research: jailbreak-extraction — 2026-05-23T09-13

## Domain: jailbreak-extraction (index 3, fourth pass)
## Focus: Cipher-encoded jailbreaks, encoding-based prompt extraction, multilingual bypasses

Prior passes covered:
- Pass 1 (2026-05-13T08-30): Structured JSON/dict extraction, sandwich attack, autonomous LLM-vs-LLM jailbreaks.
- Pass 2 (2026-05-10): DIA-I affirmative prefill, hypothetical unrestricted AI, academic bypass framing.
- Pass 3 (2026-05-08): Bad Likert Judge, many-shot jailbreaks.

This pass focuses on cipher/encoding obfuscation as a jailbreak bypass technique — specifically
the "encode and execute" pattern — and on encoding-based system-prompt extraction (translating
the prompt into base64, morse, hex, etc. to evade output filters).

---

## Findings

1. **RoguePrompt: Dual-Layer Cipher Jailbreak (arxiv:2511.18790, Nov 2025 / Jan 2026)**
   - Source: https://arxiv.org/abs/2511.18790
   - RoguePrompt is an automated jailbreak pipeline that encodes a forbidden prompt in two nested
     cipher layers (ROT-13 + Vigenère) and embeds natural-language decoding instructions in the
     same payload. The model decodes the payload and executes the hidden instructions within a
     single query. Tested on 313 real-world hard-rejected prompts across multiple frontier LLMs
     (black-box, API-only access). Results: 93.93% moderation filter bypass, 79.02% successful
     instruction reconstruction, 70.18% execution success. The attack requires no knowledge of
     model weights, system prompts, or moderation rules — only standard user-level API access.
   - **aigis takeaway:** Add `jb_cipher_decode_execute` to catch prompts that ask a model to
     decode an encoded payload (base64, ROT-13, Vigenère, morse, hex, caesar) and then
     follow/execute the decoded content. The existing `pi_encoding_bypass` (score 55) only matches
     "[encoding type] + instruction/command" as separate words, not the decode-then-execute
     command structure.

2. **Encoding-Based System-Prompt Extraction (synthesis of SPE-LLM + OWASP LLM07, 2025–2026)**
   - Source: https://witness.ai/blog/llm-system-prompt-leakage/ ; https://genai.owasp.org/llmrisk/llm072025-system-prompt-leakage/
   - Attackers ask the model to translate/convert its system prompt into an encoding format
     (base64, hex, morse code, ROT-13, binary) to bypass output-side content monitors that scan
     for verbatim text. The encoded form of the system prompt is invisible to simple text-match
     guardrails applied to the response. Unit 42 (March 2026) documented live instances of this
     extraction variant on commercial platforms. The existing `jb_sandwich_extraction` (score 65)
     and `pi_system_prompt_leak` (score 45) match verbatim or structured output requests but do
     not cover the "translate to encoding" variant.
   - **aigis takeaway:** Add `jb_encode_prompt_extraction` to catch "translate/convert/encode your
     system prompt to [base64/hex/morse/ROT-13/binary]" requests, which are system-prompt
     extraction attempts designed to bypass output filters.

3. **JBFuzz — Fuzzing-Based Jailbreaking with 99% ASR (arxiv:2503.08990, Mar 2025)**
   - Source: https://arxiv.org/abs/2503.08990
   - JBFuzz applies software fuzzing techniques to jailbreaking. It generates mutations of seed
     jailbreak templates and uses a lightweight evaluator for feedback. Achieved ~99% average
     attack success rate across GPT-4o, Gemini 2.0, DeepSeek-V3 in under 60 seconds per query.
     No new single-pattern rule actionable (mutations are diverse); the research confirms that
     broader rule coverage is the correct approach for rule-based guards.
   - **aigis takeaway:** No single pattern covers JBFuzz (mutation diversity too broad). Confirms
     importance of layered rule coverage rather than single silver-bullet rules.

4. **Multilingual Jailbreak via Low-Resource African Languages (arxiv:2605.18239, May 2026)**
   - Source: https://arxiv.org/abs/2605.18239
   - Multi-turn conversations using low-resource African languages (Afrikaans, Kiswahili,
     isiXhosa, isiZulu) bypass safety mechanisms across ChatGPT, Claude, DeepSeek, Gemini, Grok.
     English: 52.7–83.6% bypass; Afrikaans: 60–78.2% bypass; Kiswahili: 41.8–70.9% bypass.
     Human red-teaming raises rates further from 59.8% to 75.8%. The vulnerability is caused by
     safety training focused on English, leaving low-resource languages under-aligned.
   - **aigis takeaway:** Multilingual bypass is a real threat. Japanese and Korean patterns are
     already implemented; Afrikaans/Swahili patterns would be extremely narrow (few attackers use
     them deliberately against AI agents). Flag for future multilingual detector expansion.
     Not actionable this cycle as a regex without high false-positive risk.

5. **Large Reasoning Models as Autonomous Jailbreak Agents (Nature Communications, 2026)**
   - Source: https://www.nature.com/articles/s41467-026-69010-1
   - DeepSeek-R1, Gemini 2.5 Flash, Grok 3 Mini, and Qwen3 235B autonomously jailbreak other
     LLMs with 97.14% overall success rate across nine target models, with no human supervision.
     The attacker reasoning model receives instructions via a system prompt and then conducts
     multi-turn conversations. Claude showed lowest vulnerability (2.86% ASR).
   - **aigis takeaway:** Autonomous multi-turn jailbreaks are behavioral, not detectable in
     single-turn regex mode. Confirms value of broad rule coverage to reduce attacker surface.
     No new regex pattern actionable.

6. **RogueGPT and Universal Adversarial Suffixes (Wiley Engineering Reports, 2026)**
   - Source: https://onlinelibrary.wiley.com/doi/10.1002/eng2.70069
   - Universal adversarial suffixes (gradient-based GCG, AutoDAN) can be appended to any harmful
     query to force compliance. Some transferable suffixes generalize across models. Detection:
     adversarial suffix patterns are model-specific and change frequently — regex is insufficient.
   - **aigis takeaway:** Adversarial suffix detection requires ML-based classifiers. Out of scope
     for zero-runtime-dependency rule-based firewall. Defer to pending.

7. **Encoding-Bypass Attack Success Rate Baseline (multiple sources, 2026)**
   - Source: https://reddogsecurity.substack.com/p/llm-security-in-2026-a-complete-attack
   - Simple encoding tricks (base64, hex, ROT-13) achieved 76.2% ASR in a study of 1,400+
     adversarial prompts. Improved decode-and-rescreen guardrails now catch common encodings at
     runtime, but the "decode-and-execute" instruction structure remains a gap for many input-side
     filters that only check encoding-word presence, not the execution intent.
   - **aigis takeaway:** Confirms that `pi_encoding_bypass` (score 55, existing) is insufficient —
     it matches "[encoding] instruction/command" but not "[decode this encoding] and [follow it]".
     Validates `jb_cipher_decode_execute` as an additive hardening.

---

## Candidate Hardenings

1. **`jb_cipher_decode_execute`** (input filter, score 65) — Detects the decode-and-execute
   attack structure from RoguePrompt (arxiv:2511.18790): prompt asks the model to decode a
   cipher-encoded payload (base64, ROT-13, Vigenère, morse, hex, caesar) and then follow/execute
   the decoded content. Complements existing `pi_encoding_bypass`. **→ TARGET FOR IMPLEMENTATION**

2. **`jb_encode_prompt_extraction`** (input filter, score 65) — Detects system-prompt extraction
   via encoding: asks the model to translate/convert its system prompt into an encoding format
   (base64, hex, morse, ROT-13, binary) to bypass output-side content filters. Complements
   `jb_sandwich_extraction` and `pi_system_prompt_leak`. **→ TARGET FOR IMPLEMENTATION**

3. *(pending)* Multilingual jailbreak patterns (Afrikaans, Kiswahili, isiXhosa, isiZulu) —
   feasible as regex keyword matchers for language-specific script or common override phrases,
   but false-positive risk needs careful calibration with native speakers.

4. *(pending)* Adversarial suffix detection — requires ML classifier; out of scope for
   zero-runtime-dependency rule-based firewall.
