# Research: jailbreak-extraction — 2026-05-23T00-22

## Domain: jailbreak-extraction (index 3, fourth pass)
## Focus: Cipher-based jailbreaks, persuasion/persona attacks, multi-turn escalation

Prior cycles covered:
- Cycle 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Cycle 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Cycle 3 (2026-05-13): Structured JSON/Dict System-Prompt Extraction, Extended Sandwich Attack, Autonomous LLM-vs-LLM Jailbreaking.

This pass targets cipher/encoding-based decode-and-execute jailbreaks, persuasion/persona prompt attacks, and the Crescendo multi-turn escalation technique.

---

## Findings

- **RoguePrompt — Dual-Layer Cipher Decode-and-Execute (arxiv:2511.18790, Nov 2025 / Jan 2026)**:
  Tafreshian introduces an automated jailbreak pipeline that applies nested ROT-13 + Vigenère
  cipher encoding to a forbidden prompt and then includes natural-language decoding instructions
  in the same query. The model decodes the ciphertext and complies with the original harmful
  instruction. Tested on 313 hard-rejected real-world prompts; achieved 93.93% filter bypass,
  79.02% content reconstruction, and 70.18% execution success across GPT-4o, Claude, Gemini,
  and Llama under black-box conditions. The core detection gap: existing `enc_rot13_instruction`
  (score 40) fires on a cipher label but does not check for the execute-after-decode intent
  signal that distinguishes this attack from harmless cipher education.
  - Source: https://arxiv.org/abs/2511.18790
  - **aigis takeaway:** Add `jb_cipher_decode_execute` pattern matching cipher name + decode
    verb + "then respond/follow/execute". (**IMPLEMENTED**)

- **Crescendo Multi-Turn Jailbreak (USENIX Security 2025, arxiv:2404.01833)**:
  Microsoft researchers show that gradually escalating through mostly benign prompts ("crescendo")
  achieves 98% ASR on GPT-4 and 100% on Gemini-Pro. Each turn moves the model slightly further
  toward harmful output, exploiting the model's tendency to follow conversational momentum. A
  fully automated variant (Crescendomation) outperforms other SOTA jailbreaks by 29-61% on
  GPT-4. Key detection challenge: harmful-classification rates drop from 60-80% (single-turn)
  to 10-20% (final Crescendo turn) on standard input filters.
  - Source: https://arxiv.org/abs/2404.01833
  - **aigis takeaway:** Multi-turn behavioral detection is required; single-turn regex cannot
    catch Crescendo. The cross-session correlator is the right place for this. Pending.

- **Persuasion / Persona Prompt Jailbreak (arxiv:2507.22171, NeurIPS 2025)**:
  Zhang et al. show that evolved persona prompts (claiming to be an expert, authority figure,
  or specific professional) reduce LLM refusal rates by 50-70% across multiple models. A genetic
  algorithm automatically crafts persona prompts, and combining persona + existing jailbreaks
  increases ASR by a further 10-20%. Overlaps somewhat with `jb_academic_research_bypass`, but
  the evolved persona variants use non-academic authority claims (doctor, lawyer, government
  official, developer) and are more varied.
  - Source: https://arxiv.org/abs/2507.22171
  - **aigis takeaway:** The academic_research_bypass pattern covers the academic framing well.
    Generic authority persona claims (doctor, government official) without paired harmful
    content keywords are too broad for a regex; false-positive risk is high. Pending.

- **Psychological Manipulation Jailbreak (arxiv:2512.18244, Dec 2025)**:
  Liu & Lin introduce Human-like Psychological Manipulation (HPM), a multi-turn black-box
  jailbreak that profiles a model's psychological vulnerabilities and constructs tailored
  manipulation strategies (flattery, false urgency, guilt framing, gaslighting). Primary
  detection challenge: psychological state manipulation is stateful and multi-turn; no reliable
  regex surface in single-turn inputs.
  - Source: https://arxiv.org/abs/2512.18244
  - **aigis takeaway:** Cross-session behavioral analysis required. Single-turn regex coverage
    is insufficient for this attack class. Pending.

- **Cipher Jailbreak Landscape — ROT-13, Vigenère, Caesar, Atbash (arxiv:2402.10601)**:
  Named cipher jailbreaks exploit the model's ability to decode text encoded in common classical
  ciphers. The Word-Substitution Cipher (WSC) framework achieves up to 60% ASR on GPT-4o. The
  LACE framework (layering WSC with other methods) adds 38% improvement on GPT-4o. The common
  thread across all variants: the attacker instructs the model to decode the cipher and then act
  on the decoded content.
  - Source: https://arxiv.org/abs/2402.10601
  - **aigis takeaway:** Confirms that cipher + decode + execute is the key three-part signal.
    The `jb_cipher_decode_execute` pattern covers ROT-13, Vigenère, Caesar, and Atbash, which
    together represent the most-studied classical ciphers in this attack class.

- **Bypassing Prompt Injection and Jailbreak Detection via Invisible Characters (arxiv:2504.11168)**:
  Shows that Unicode Tag Block (U+E0000-U+E007F) and Variation Selector Supplement characters
  achieve 90% bypass of Azure Prompt Shield and Meta Prompt Guard. aigis already covers this via
  `enc_tag_block_ascii` and `te_unicode_tag_smuggling`. Confirmed as already mitigated.
  - Source: https://arxiv.org/abs/2504.11168
  - **aigis takeaway:** Already covered by existing patterns; no action needed.

---

## Candidate Hardenings

1. **`jb_cipher_decode_execute`** (input, score 60) — Named cipher (ROT-13, Vigenère, Caesar,
   Atbash) + decode verb + then-execute intent signal. Covers the RoguePrompt attack class
   (93.93% filter bypass, arxiv:2511.18790). **→ IMPLEMENTED**

2. *(pending)* Crescendo multi-turn escalation detection — requires cross-turn behavioral analysis
   in the session correlator; not addressable via single-turn regex.

3. *(pending)* Persuasion/persona authority claim + harmful content pairs — partially covered by
   `jb_academic_research_bypass`; expanding to other authority claims (doctor, government official)
   risks false positives without more specific harmful content anchors.

4. *(pending)* Psychological manipulation (HPM) — multi-turn stateful attack; requires session-
   level correlator.
