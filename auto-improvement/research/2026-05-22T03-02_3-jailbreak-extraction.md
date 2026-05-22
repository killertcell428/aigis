# Research: jailbreak-extraction — 2026-05-22T03-02

## Domain: jailbreak-extraction (index 3, fourth pass)
## Cycle timestamp: 2026-05-22T03-02
## Focus: Payload splitting, adversarial creative framing, and emerging jailbreak
##        techniques for 2025–2026

Prior passes covered:
- Cycle 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Cycle 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass.
- Cycle 3 (2026-05-13): Structured JSON/dict system-prompt extraction, Sandwich attack.

This pass targets two deferred pending items (payload splitting and creative-format jailbreaks)
plus a fresh scan of 2025–2026 literature for new jailbreak techniques not yet covered.

---

## Findings

- **Payload Splitting / "Speak Easy" (arxiv:2502.04322, ICML 2025)**: Decomposing a harmful
  request into multiple numbered sub-steps that each appear innocuous raises GPT-4o's attack
  success rate from 9.2% to 55.5%. When combined with multilingual translation, the combined
  ASR exceeds 90%. No single step triggers safety filters; the danger is only visible in the
  full numbered sequence — especially in step 3 or later where the harmful topic appears.
  - Source: https://arxiv.org/abs/2502.04322
  - **aigis takeaway:** Implement `jb_payload_splitting` — detect numbered multi-step prompts
    where a harmful keyword (synthesis, exploit, malware, weapon) appears in step 3 or later.
    (**IMPLEMENTED**)

- **Adversarial Poetry / Creative Format Jailbreak (arxiv:2511.15304, Nov 2025)**: Encoding
  harmful requests in poetic form (ballad, rap, haiku, limerick, sonnet, song) achieves 62%
  average ASR across 25 frontier models with hand-crafted poems. An automated meta-prompt that
  converts any of the MLCommons 1,200 harmful prompts into verse achieves 43% ASR with zero
  manual effort. Coverage in The Register (Nov 2025): "LLMs can be easily jailbroken using
  poetry." Models optimised for creative assistance are especially susceptible.
  - Source: https://arxiv.org/abs/2511.15304
  - **aigis takeaway:** Implement `jb_poetry_harmful_framing` — detect creative-format requests
    (write/compose/create + poem/rap/ballad/haiku/etc.) combined with a harmful how-to or
    dangerous subject within ~200 chars. (**IMPLEMENTED**)

- **Tree of Attacks with Pruning (TAP, arxiv:2312.02119) — still widely used in 2025**:
  TAP automates multi-round jailbreak refinement using LLM-as-attacker: it generates candidate
  prompts, prunes low-probability branches, and iteratively refines. Combined with payload
  splitting ("Speak Easy"), TAP exceeds 0.9 ASR on frontier models. TAP payloads often look
  like legitimate research or indirect requests when no direct keyword is present.
  - Source: https://arxiv.org/abs/2312.02119
  - **aigis takeaway:** Single-turn regex cannot fully stop TAP; but covering the payload
    surface that TAP exploits (creative framing, step decomposition) reduces its search space.
    No new rule needed specifically for TAP itself.

- **Prompt Injection via Translation Requests ("Translate this text: ...")**: A documented
  evasion technique where the attacker embeds a harmful instruction inside a "translate this
  text" framing. The outer request looks benign (translation), but the inner content contains
  the actual attack payload. Confirmed by Anthropic red-team guidance (2025) and reproduced in
  OWASP GenAI Q1 2026 Appendix B.
  - Source: https://owasp.org/www-project-top-10-for-large-language-model-applications/
  - **aigis takeaway:** Borderline for a simple regex rule — the harmful content needs to be
    extracted from the translation payload. Deferred; needs structural payload extraction.

- **Crescendo / Gradual Escalation (arxiv:2404.01833, USENIX Security 2025)**: Multi-turn
  attack where each turn appears benign but the conversation gradually escalates to harmful
  content. A 2025 follow-up showed >70% ASR against models hardened only for single-turn
  attacks. Already documented in `pending/2026-05-08_crescendo-multiturn-detection.md` — still
  requires a stateful multi-turn tracker (>100 LOC) not suitable for a single cycle.
  - Source: https://arxiv.org/abs/2404.01833
  - **aigis takeaway:** Remains in pending; the stateful API change exceeds the 100-LOC limit.

- **Persona Injection via Emotional Manipulation (PHISH, arxiv:2601.16466, Jan 2026)**:
  Gradually induces an adversarial AI persona through semantically loaded questions over many
  turns, without any explicit jailbreak phrase. Targets deployed assistants in mental-health,
  education, and customer-service contexts. No identifiable single-turn fingerprint.
  - Source: https://arxiv.org/abs/2601.16466
  - **aigis takeaway:** Multi-turn behavioral detection needed; beyond single-turn regex scope.
    No new rule implemented.

- **Virtualization / Nested Context Jailbreak**: Attacker creates a "simulation" or "virtual
  environment" within the prompt and asks the AI to "run" a hypothetical AI inside it. Distinct
  from the `jb_hypothetical_ai` rule (which targets explicit "uncensored AI" framing) — this
  variant uses neutral virtual-machine or sandbox language. Documented in WildJailbreak
  (arxiv:2405.05555, May 2024) dataset, still active in 2025 wild datasets.
  - Source: https://arxiv.org/abs/2405.05555
  - **aigis takeaway:** A new `jb_virtualization` pattern could cover "simulate/run/execute
    a virtual AI/agent that …" phrasing. Deferred to next cycle — needs careful FP tuning for
    legitimate simulation prompts.

- **Base64 / Encoding-Based Jailbreaks (multiple sources, 2025)**: Encoding harmful content in
  Base64, ROT13, or other encodings to bypass text-level filters. aigis already has
  `pi_encoding_bypass` (for generic encoding) and `eo_base64_injection` (for Base64). Coverage
  for using Base64 as a jailbreak delivery mechanism (encode the jailbreak, ask the model to
  decode and follow) is partial — the current rules detect Base64 in content but do not
  specifically flag the decode-and-execute instruction pattern.
  - Source: Multiple, including OWASP LLM07 (2025 update)
  - **aigis takeaway:** Enhancement to the existing `eo_base64_injection` rule to also flag
    "decode this base64 and execute/follow/apply the instructions" phrasing. Deferred pending
    investigation of existing rule coverage.

---

## Candidate Hardenings

1. **`jb_payload_splitting`** (input, score 45) — Step-enumerated decomposition attack.
   → **IMPLEMENTED this cycle**

2. **`jb_poetry_harmful_framing`** (input, score 55) — Creative-format jailbreak via
   poem/rap/ballad + harmful subject.
   → **IMPLEMENTED this cycle**

3. **`jb_virtualization`** (input, score ~55) — Nested virtual AI / simulation jailbreak.
   → Deferred: needs FP tuning for legitimate simulation prompts.

4. **`eo_base64_decode_execute`** (input, score ~60) — "Decode this Base64 and follow the
   instructions" pattern, closing a gap in existing encoding-bypass coverage.
   → Deferred: needs investigation of coverage overlap with existing `eo_base64_injection`.

5. **Translation-wrapper injection** — Harmful payload embedded in a translation request.
   → Deferred: requires structural payload extraction, not just surface regex.
