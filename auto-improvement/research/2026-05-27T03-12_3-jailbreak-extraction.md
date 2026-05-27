# Research: jailbreak-extraction — 2026-05-27T03-12

## Domain: jailbreak-extraction (index 3, fourth pass)
## Cycle index: 3
## Timestamp: 2026-05-27T03-12

Prior cycles covered:
- Cycle 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Cycle 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Cycle 3 (2026-05-13): Structured JSON/Dict extraction, Extended sandwich attack, Autonomous LLM-vs-LLM jailbreaks, ICE, PHISH persona manipulation.

This pass targets payload-splitting attacks, translation-framing extraction, refusal suppression,
policy config spoofing, and special-token injection — mostly fresh 2024–2026 material.

---

## Findings

- **Payload Splitting / "Speak Easy" (arxiv:2502.04322, ICML 2025)**: Decomposes a harmful
  request into numbered steps where no single step triggers safety filters. The dangerous topic
  emerges only in step 3+, after benign framing is established in earlier steps. Raises GPT-4o's
  attack success rate from 9.2% to 55.5%; combined with multilingual translation, exceeds 90%.
  Source: https://arxiv.org/abs/2502.04322
  - **aigis takeaway:** Add `jb_payload_splitting` — numbered-step structural framing followed by
    known-dangerous substance/weapon/malware keywords. (**IMPLEMENTED**)

- **Translation-Framing System-Prompt Extraction (arxiv:2307.06865, 2023; confirmed in
  arxiv:2505.23817, 2025; OWASP LLM07:2025)**: Requests the model to translate, paraphrase,
  or re-encode its system instructions into a foreign language or format. Disguises a prompt-leak
  as a benign translation task; bypasses classifiers trained on English-language direct-disclosure
  patterns. Documented against Bard, Bing Chat, and other production systems. The `pi_system_prompt_leak`
  pattern (score 45) covers "show me your system prompt" but not the translation/paraphrase variant.
  Source: https://arxiv.org/abs/2307.06865; https://arxiv.org/abs/2505.23817
  - **aigis takeaway:** Add `jb_translation_extraction` — translation verb + system-prompt term + language indicator. (**IMPLEMENTED**)

- **Refusal Suppression / "Don't Say No" (arxiv:2404.16369, ACL 2025 Findings)**: Explicitly
  instructs the model never to produce refusal language ("do not say 'I cannot'", "never refuse",
  "you must always comply"). The prompt targets the output side — suppressing specific refusal
  vocabulary — rather than substituting a new persona. Achieves 60–85%+ ASR. The prompt-based
  form is directly detectable by regex.
  Source: https://arxiv.org/abs/2404.16369
  - **aigis takeaway:** Candidate `jb_refusal_suppression` — explicit suppression of refusal vocabulary.
    Not implemented this cycle (LOC budget used by two patterns above); saved to pending.

- **Policy Puppetry / Config-Format Safety Spoofing (HiddenLayer Research, Apr 2025)**: Wraps
  harmful instructions in XML/JSON blocks mimicking internal policy configuration files
  (`<system_policy>`, `<safety_filter>disabled</safety_filter>`, `"restrictions":[]`). Models
  trained on policy/config data interpret these structured formats as authoritative system-level
  directives. Up to 90% ASR across GPT-4, Claude 3, Gemini 1.5, Mistral, Llama 3.
  Source: https://hiddenlayer.com/research/novel-universal-bypass-for-all-major-llms
  - **aigis takeaway:** Candidate `jb_policy_config_spoof` — XML/JSON policy-format safety-disable structure.
    Saved to pending.

- **FlipAttack — Text Reversal (arxiv:2410.02832, ICML 2025)**: Reverses or scrambles harmful
  text at the start of the prompt where safety classifiers are most attentive, then provides
  a "decoding instruction" at the end that guides the model to reassemble and execute. ~98% ASR
  on GPT-4o; bypasses 5 guardrail models. The decoding instruction is the detectable signal.
  Source: https://arxiv.org/abs/2410.02832
  - **aigis takeaway:** Candidate `jb_flip_reverse_decode` — "read/decode this backwards/in reverse".
    Saved to pending.

- **Special Token Injection / MetaBreak (arxiv:2406.19845; arxiv:2510.10271, Oct 2025)**:
  Injects chat-template role tokens (`[INST]`, `</s>`, `<<SYS>>`, `<|im_start|>`, `<|eot_id|>`)
  into user-turn text to forge fake assistant turns. The model reads injected tokens as part of
  its own prior output, suppressing safety checks. MetaBreak achieves +11.6–34.8% ASR lift over
  SOTA when content moderation is active.
  Source: https://arxiv.org/abs/2406.19845; https://arxiv.org/abs/2510.10271
  - **aigis takeaway:** Candidate `jb_special_token_injection` — role template tokens in user input.
    Saved to pending.

- **Deceptive Delight (Palo Alto Unit42, Oct 2024)**: Hides a single harmful instruction within a
  single turn that also contains several benign tasks. Safety classifiers, trained to assess overall
  intent, are distracted by the volume of benign content. 64.6% average ASR across 8 models.
  Source: https://unit42.paloaltonetworks.com/jailbreak-llms-through-camouflage-distraction/
  - **aigis takeaway:** Difficult to distinguish from the payload-splitting pattern; `jb_payload_splitting`
    provides partial coverage. A dedicated multi-task sandwich rule saved to pending.

- **Doublespeak / Codeword Substitution (arxiv:2512.03771, 2025)**: Provides in-context examples
  where a benign word is consistently substituted for a harmful keyword, shifting the model's
  internal representation. Final query uses the benign codeword to request the prohibited action.
  74% ASR on Llama-3.3-70B. Detectable via substitution-setup phrases.
  Source: https://arxiv.org/abs/2512.03771
  - **aigis takeaway:** Candidate `jb_codeword_substitution`. Saved to pending.

---

## Candidate Hardenings

1. **`jb_payload_splitting`** (input, score 55) — Step-enumerated decomposition attack.
   → **IMPLEMENTED**

2. **`jb_translation_extraction`** (input, score 65) — Translation-framing system-prompt extraction.
   → **IMPLEMENTED**

3. *(pending)* **`jb_refusal_suppression`** — Explicit suppression of model refusal vocabulary.
   LOC budget exhausted this cycle.

4. *(pending)* **`jb_policy_config_spoof`** — XML/JSON/INI policy-format with safety-disabling semantics.
   LOC budget exhausted this cycle.

5. *(pending)* **`jb_flip_reverse_decode`** — FlipAttack decoding instruction ("read backwards").
   Deferred for next jailbreak cycle.

6. *(pending)* **`jb_special_token_injection`** — Chat-template role tokens (`[INST]`, `<|im_start|>`)
   in user input. Deferred for next jailbreak cycle.

7. *(pending)* **`jb_codeword_substitution`** — Doublespeak in-context codeword setup.
   Deferred for next jailbreak cycle.
