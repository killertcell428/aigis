# Research: jailbreak-extraction — 2026-05-26T00-07

## Domain: jailbreak-extraction (index 3, fourth pass)
## Focus: Task-in-Prompt (TIP) cipher attacks, LogiBreak, multilingual jailbreaks, JBFuzz fuzzing

Prior cycles covered:
- Cycle 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Cycle 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Cycle 3 (2026-05-13): Structured JSON/Dict System-Prompt Extraction, Sandwich Attack (verbatim qualifier).

This pass targets task-in-prompt encoding attacks, logic-notation jailbreaks, multilingual
low-resource-language bypasses, and automated fuzzing-based jailbreaks documented in
2025–2026 research.

---

## Findings

- **Task-in-Prompt (TIP) Attacks — Cipher Decode-and-Execute (arxiv:2501.18626, ACL 2025)**:
  A novel class of jailbreak attacks that embeds a sequence-to-sequence task (cipher decoding,
  riddle solving, code execution) into the prompt. The attacker names an encoding scheme
  (Base64, ROT-13, Caesar, hex, custom cipher), provides encoded harmful content, and instructs
  the model to decode it and then execute the decoded instructions. Safety classifiers trained
  on natural-language harmful content fail because the surface text appears to be a benign
  "decode this" request. The PHRYGE benchmark showed the technique successfully bypassed
  six state-of-the-art models including GPT-4o and LLaMA 3.2 (published ACL 2025, authors
  Berezin et al. from Télécom SudParis).
  - Source: https://arxiv.org/abs/2501.18626
  - **aigis takeaway:** Add `jb_tip_cipher_decode` pattern matching cipher/encoding name +
    decode directive + execute/follow instruction sequence. The existing `pi_encoding_bypass`
    only matches `(encoding_type) (instruction|command)` immediately adjacent; it does not
    cover the three-part decode-and-execute flow. (**SELECTED FOR IMPLEMENTATION**)

- **JBFuzz — Fuzzing-Based Automated Jailbreak (arxiv:2503.08990, March 2025)**:
  JBFuzz applies binary-fuzzing techniques to jailbreak LLMs. It uses seed prompt templates
  and a lightweight mutation engine to evolve increasingly effective jailbreak prompts in a
  black-box setting. Average ASR of 99% across GPT-4o, Gemini 2.0, DeepSeek-V3 in roughly
  7 queries / 60 seconds. Llama-2 was hardest at 91% ASR. The attack is mutation-based and
  model-agnostic; no single fixed regex can capture all its outputs.
  - Source: https://arxiv.org/abs/2503.08990
  - **aigis takeaway:** JBFuzz generates diverse jailbreak prompts that span multiple existing
    categories (roleplay, restriction-bypass, fictional framing). No new single-regex detection
    rule is appropriate; coverage comes from the breadth of existing rules. The finding
    reinforces the importance of scoring multiple pattern matches cumulatively rather than
    relying on any one rule.

- **Logic Jailbreak (LogiBreak) — Formal Logical Expression Bypass (arxiv:2505.13527, May 2025)**:
  LogiBreak converts harmful natural-language prompts into formal logical notation using Unicode
  symbols (∀, ∃, ⟹, ∴, ¬, ∧, ∨) or spelled-out equivalents ("for all", "there exists",
  "implies", "therefore"). Safety fine-tuning datasets do not include formal logic notation,
  so the model's safety refusals are less reliable for logic-form inputs. Evaluated on a
  multilingual jailbreak dataset across three languages.
  - Source: https://arxiv.org/abs/2505.13527
  - **aigis takeaway:** A regex targeting `∀|∃|⟹|∴` combined with override/output imperatives
    could detect the most extreme form. However, these symbols also appear in legitimate
    mathematical proofs, making false-positive tuning difficult without a threshold on surrounding
    context. Deferred to pending — not implemented this cycle.

- **Multilingual Jailbreaking via Low-Resource African Languages (arxiv:2605.18239, May 2026)**:
  Researchers at Stellenbosch University tested whether multi-turn conversations in Afrikaans,
  Kiswahili, isiXhosa, and isiZulu bypass commercial LLM safety mechanisms. Single-turn
  translation attacks were ineffective, but multi-turn conversations achieved harmful response
  rates of 52.7% (Claude 3.5 Haiku) to 83.6% (GPT-4o-mini) in English, and 41.8–78.2% in
  the African languages. Human red-teaming pushed average ASR from 59.8% to 75.8%.
  - Source: https://arxiv.org/abs/2605.18239
  - **aigis takeaway:** This is a multi-turn, language-detection-dependent attack. Rule-based
    single-turn regex cannot reliably identify low-resource-language content without a language
    ID model, which would add a runtime dependency. Deferred to pending.

- **Crescendo Multi-Turn Jailbreak (arxiv:2404.01833, USENIX Security 25)**:
  The Crescendo attack begins with a benign abstract question, then gradually escalates over
  multiple turns using phrases like "Great, now write about [slightly more specific topic]"
  until the model produces harmful content it would have refused at turn 1. Published at
  USENIX Security 2025 by Russinovich et al. (Microsoft).
  - Source: https://arxiv.org/abs/2404.01833
  - **aigis takeaway:** The escalation pattern is multi-turn and requires conversation-level
    context to detect reliably. Single-turn regex coverage would produce high false positives
    ("Great, now write a poem" is benign). Deferred to pending.

- **ACE/LACE Custom Cipher Jailbreaks (arxiv:2402.10601, updated 2025)**:
  Attack using Custom Encryptions (ACE) and Layered Attack using Custom Encryptions (LACE)
  encode harmful queries in novel user-created ciphers, then layer multiple ciphers to increase
  ASR. GPT-4o-mini ASR: 60%, Llama-3.1-8B-Instruct: 88%, Gemini-1.5-Flash: 66%. LACE
  improved GPT-5 ASR from 0% to 8%.
  - Source: https://arxiv.org/abs/2402.10601
  - **aigis takeaway:** The `jb_tip_cipher_decode` pattern implemented this cycle covers both
    ACE and LACE variants (it explicitly matches "custom cipher/encryption/encoding").

---

## Candidate hardenings

1. **`jb_tip_cipher_decode`** (input filter, score 55) — Detect Task-in-Prompt cipher
   decode-and-execute attacks. Match: cipher/encoding type + decode instruction + execute/follow
   the decoded task. Covers Base64, ROT-N, Caesar, atbash, Vigenère, morse, hex-encoded,
   binary-encoded, and custom ciphers. **SELECTED — implemented this cycle.**

2. **LogiBreak Unicode operator detection** — Match ∀/∃/⟹ symbols combined with
   override language. **DEFERRED** — false-positive risk in mathematical discussions;
   needs tighter context scoring.

3. **Multilingual low-resource-language jailbreak detection** — Language-ID integration
   to flag low-resource-language queries alongside harmful keywords. **DEFERRED** — requires
   runtime language detection dependency (violates zero-dependency constraint).

4. **Crescendo multi-turn escalation scoring** — Assign elevated risk when a message
   contains "great, now [harmful topic]" after prior high-risk turns. **DEFERRED** —
   requires conversation-level state, not supported in single-turn `scan()`.
