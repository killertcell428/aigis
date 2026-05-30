# Research: Jailbreak & System Prompt Extraction (Cycle 3, Fourth Pass)

**Domain:** `jailbreak-extraction` (index 3)
**Cycle start UTC:** 2026-05-30T06-17
**Prior cycle 3 files:**
- `2026-05-08T05-49_3-jailbreak-extraction.md` — Bad Likert Judge, Many-Shot (implemented)
- `2026-05-10T12-00_3-jailbreak-extraction.md` — Affirmative prefill, Hypothetical AI, Academic bypass (implemented); poetry + payload splitting (deferred)
- `2026-05-13T08-30_3-jailbreak-extraction.md` — Structured extraction, Sandwich attack (implemented); poetry + payload splitting (still pending)

**This pass focus:** Implement two pending jailbreak patterns deferred from prior cycles plus one fresh finding (SATA), and document new 2026 research for future cycles.

**Sources consulted:** arXiv (2025–2026), Palo Alto Unit 42, HarmBench, WildJailbreak, ICML 2025 proceedings, ACL Findings 2025, LLMSec 2025 workshop, prior pending files

---

## Key Findings

- **Adversarial Poetry / Creative Format Jailbreaking** (arxiv:2511.15304, November 2025):
  Encoding harmful requests in poetic form (rap, ballad, haiku, limerick, ode) achieves 62%
  average ASR across 25 frontier models. An automated meta-prompt that converts any of the
  MLCommons 1,200 harmful prompts into verse achieves 43% ASR with no manual effort.
  The existing `jb_fictional_bypass` pattern requires the harmful keyword within 100 chars of
  the fictional framing; poetry directives often run longer, placing the dangerous subject after
  the creative instruction. This gap was confirmed in the pending file from the prior cycle.
  - Source: https://arxiv.org/abs/2511.15304
  - **aigis takeaway:** Add `jb_poetry_harmful_framing`: `write/compose/create` + `poem/rap/ballad/haiku/...` + dangerous keyword within 200 chars. **→ IMPLEMENTED**

- **Payload Splitting / Speak Easy** (ICML 2025, arxiv:2502.04322, February 2025):
  Decomposes a harmful request into multiple numbered steps, each individually benign.
  GPT-4o ASR increases from 9.2% to 55.5% with this technique alone; combined with TAP-T,
  exceeds 90%. The pattern exploits that safety filters evaluate each step independently.
  A three-step decomposition with a dangerous keyword appearing only in step 3 or later is the
  minimum to form a recognizable signal.
  - Source: https://arxiv.org/abs/2502.04322
  - **aigis takeaway:** Add `jb_payload_splitting`: three numbered steps (step/part/phase/task 1, 2, 3+) + dangerous keyword in step 3+. **→ IMPLEMENTED**

- **Persona Jailbreaking — PHISH** (arxiv:2601.16466, January 2026):
  Gradually induces an adversarial persona via semantically loaded cues over multiple conversation
  turns, with no explicit jailbreak phrase. Targets deployed personas in education, mental health,
  and customer service domains. Effective only across multiple conversation turns — not detectable
  in single-turn input filters.
  - Source: https://arxiv.org/abs/2601.16466
  - **aigis takeaway:** Requires stateful multi-turn behavioral detection. Out of scope for
    rule-based single-input filtering. Cross-session correlator roadmap.

- **Echo Chamber Multi-Turn Jailbreak** (arxiv:2601.05742, NeuralTrust, January 2026):
  Three-phase attack where the model is guided to elaborate on its own prior outputs until
  harmful content is produced. Over 90% ASR for violence, hate, pornography; 80% for
  misinformation. No explicit jailbreak phrase used in any single turn.
  - Source: https://arxiv.org/abs/2601.05742
  - **aigis takeaway:** Single-turn detection is impossible — requires session-level state tracking.
    Noted for the cross-session correlator roadmap.

- **Autonomous LLM-vs-LLM Jailbreaking** (Nature Communications, 2026):
  Large reasoning models (DeepSeek-R1, Gemini 2.5 Flash, Grok 3 Mini, Qwen3) can autonomously
  jailbreak other LLMs with 97.14% overall success rate across nine target models including GPT-4o
  and Claude 4 Sonnet, with no human intervention. Claude showed the lowest vulnerability (2.86%
  ASR). Autonomous jailbreaks iterate over multi-turn conversations — not regex-detectable in a
  single-input filter.
  - Source: https://redteams.ai/blog/llm-jailbreaking-2026
  - **aigis takeaway:** Confirms that broader rule coverage (reducing the attack surface that
    automated jailbreakers can exploit) is the correct defense posture for rule-based systems.

- **DictAttack / Control-Plane Jailbreaks via JSON Schema** (arxiv:2503.24191, March 2025;
  arxiv:2510.17904 BreakFun):
  Attackers embed harmful intent at the JSON Schema level (enum constraints, grammar rules)
  while keeping the text prompt entirely benign. DictAttack achieves 94–99% ASR on GPT-5 and
  Gemini 2.5. These attacks operate at the constrained-decoding layer — regex detection on the
  input text is insufficient.
  - Source: https://arxiv.org/abs/2503.24191; https://arxiv.org/abs/2510.17904
  - **aigis takeaway:** Infrastructure-level defense (schema validation, constrained-decoding
    audit). Pending: a hardening guide rather than a detection pattern.

- **SATA — Simple Assistive Task Linkage** (arxiv:2412.15289, ACL Findings 2025):
  Harmful keywords are replaced with `[MASK]` tokens borrowed from BERT/NLP notation.
  The actual dangerous term is embedded inside a benign "assistive sub-task": either a
  fill-in-the-blank passage where the model reconstructs the masked word, or a list where
  the model looks up an element at a given position index. The model reasons through the
  innocent-looking task and thereby produces the harmful content without a direct instruction.
  Two variants: MLM (fill-in-the-blank) achieves 82–96% ASR on GPT-4o/GPT-3.5; ELP
  (list-position lookup) achieves 78–86% ASR. Claude v2: 68–86% ASR. The `[MASK]` token
  is BERT/NLP notation that legitimate users virtually never send in a chat interface.
  - Source: https://arxiv.org/abs/2412.15289
  - **aigis takeaway:** Pattern matching `\[MASK\d*\]` is near-zero false positive and catches
    both MLM and ELP variants. **→ IMPLEMENTED**

- **ICE — Intent Concealment and Diversion** (arxiv:2505.14316, ACL 2025):
  Achieves high ASR with a single query by concealing harmful intent within a benign framing and
  diverting attention with misdirection (analogies, embedded sub-tasks, benign cover stories).
  The BiSceneEval dataset introduced to evaluate this technique covers diverse concealment methods
  that resist a single unified regex pattern.
  - Source: https://arxiv.org/abs/2505.14316
  - **aigis takeaway:** The `jb_academic_research_bypass` pattern partially covers some ICE
    variants (authority framing + specific harmful term). No single new pattern closes the full
    gap. No change this cycle.

- **Unicode Emoji/Tag Smuggling for Guardrail Evasion** (arxiv:2504.11168, LLMSec 2025 @ ACL):
  Jailbreak payload is interspersed with invisible Unicode characters in ranges that LLM
  guardrail classifiers tokenize differently from the target model. Emoji smuggling achieved
  100% bypass rate against all six tested commercial guardrails (Azure Prompt Shield, Meta
  Prompt Guard, NeMo, Vijil, Protect AI v2). Unicode Tag Smuggling achieved 90.15% against
  Azure Prompt Shield. The underlying character ranges (U+FE00–U+FE0F, U+E0000–U+E007F)
  are already partially covered by `ENCODING_BYPASS_PATTERNS` in aigis — this cycle did not
  add a new pattern but confirms existing coverage is correctly scoped.
  - Source: https://arxiv.org/abs/2504.11168
  - **aigis takeaway:** Verify that `ENCODING_BYPASS_PATTERNS` covers U+FE0x variation selectors.
    If gaps exist, add a dedicated rule in a future evasion-obfuscation cycle.

---

## Candidate Hardenings

1. ✅ **`jb_poetry_harmful_framing`** (input, score 55) — `write/compose/create` + creative form
   (poem/rap/ballad/haiku/limerick/sonnet/ode/verse) + dangerous keyword within 200 chars.
   **→ IMPLEMENTED** (arxiv:2511.15304; 62% ASR hand-crafted, 43% ASR automated).

2. ✅ **`jb_payload_splitting`** (input, score 45) — Three or more numbered steps where a
   dangerous keyword appears in step 3+. **→ IMPLEMENTED** (ICML 2025, arxiv:2502.04322;
   GPT-4o ASR 9.2% → 55.5%; combined ASR >90%).

3. ✅ **`jb_sata_mask_lookup`** (input, score 60) — `[MASK]` token in user input.
   **→ IMPLEMENTED** (arxiv:2412.15289, ACL Findings 2025; GPT-4o ASR 82–96%).

4. ⏳ **PHISH persona manipulation** — Requires stateful multi-turn detection. Deferred.

5. ⏳ **Control-plane JSON Schema jailbreaks** — Requires schema-validation infrastructure, not
   regex. Pending hardening guide (see `2026-05-13_control-plane-schema-jailbreak.md`).

6. ⏳ **Echo Chamber multi-turn** — Requires cross-session correlator. Out of scope for this cycle.

7. ⏳ **Unicode emoji/tag smuggling** — Verify ENCODING_BYPASS_PATTERNS coverage; add if gaps
   found. Best addressed in the next evasion-obfuscation (index 7) cycle.
