# Research: jailbreak-extraction — 2026-05-21T06-14

## Domain: jailbreak-extraction (index 3, fourth pass)
## Focus: Keyword masking via SATA, multi-turn escalation, token-level gradient attacks

Prior cycles covered:
- Cycle 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Cycle 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass.
- Cycle 3 (2026-05-13): Structured JSON extraction, Extended sandwich attack (verbatim qualifier).

This pass targets keyword-masking/task-linkage jailbreaks (SATA), multi-turn escalation
(Crescendo/AutoAdv), and token-level adversarial suffix attacks (GCG variants).

---

## Findings

- **SATA: Simple Assistive Task Linkage (ACL 2025, arxiv:2412.15289)**: Attacker replaces harmful
  keywords with `[MASK]` bracket-notation placeholder tokens in a prompt, then asks the model to
  "fill in the blank" using a masked-language-modeling (MLM) assistive task. Because the harmful
  keyword is absent from the raw input, classifiers scanning for explicit harmful terms miss it.
  On AdvBench, the MLM-task variant achieved **85% ASR** and the position-lookup variant **76%
  ASR**. Multiple prompt forms exist: "Fill in the blank: 'How to [MASK] a server'",
  "Complete the following: '[BLANK] synthesis instructions'", "What word goes in [TOKEN]?".
  - Source: https://arxiv.org/abs/2412.15289
  - **aigis takeaway:** Add `jb_task_masking` pattern detecting bracket placeholder tokens combined
    with fill-in-the-blank task language. (**IMPLEMENTED**)

- **Crescendo Multi-Turn Escalation (USENIX Security 2025, arxiv:2404.01833)**: Starts with benign
  prompts and gradually steers the conversation toward harmful outputs across multiple turns. The
  automated variant (Crescendomation) achieves **29–61% higher success rates on GPT-4 and 49–71%
  on Gemini-Pro** compared to single-turn baselines. Individual turns appear harmless; the pattern
  is only visible at conversation level.
  - Source: https://arxiv.org/abs/2404.01833
  - **aigis takeaway:** Multi-turn behavioral detection required. Not detectable via single-turn
    regex. Roadmap item for a cross-turn correlator rule.

- **AutoAdv: Automated Adversarial Multi-Turn Prompting (arxiv:2511.02376)**: Training-free
  black-box attack using a secondary LLM (Grok-3-mini) to generate adaptive multi-turn jailbreaks.
  Achieves **95% ASR on Llama-3.1-8B within six turns** with adaptive pattern learning. Impossible
  to detect via input regex; requires behavioral analysis.
  - Source: https://arxiv.org/html/2511.02376v1
  - **aigis takeaway:** Out of scope for rule-based single-turn filter. Cross-session correlator
    roadmap.

- **Token-Level Gradient-Based Attacks / GCG Variants (arxiv:2508.14853, arxiv:2412.08615)**:
  White-box gradient attacks systematically optimize adversarial token suffixes using first-order
  Taylor approximation. Recent variants combine token replacement with attention manipulation.
  Produce gibberish-looking suffixes that are semantically aligned via gradients. Not detectable
  via regex.
  - Source: https://arxiv.org/pdf/2508.14853
  - **aigis takeaway:** Requires embedding-space or gradient-space analysis, not regex. Out of
    scope for current rule-based engine.

- **Indirect System Prompt Extraction via Refusal Quotes (Praetorian/WitnessAI, 2025-2026)**:
  Attackers trigger refusal messages that inadvertently quote the rule being violated ("I can't
  help because my instructions say..."), then extract the quoted fragment. Succeeded in ~31% of
  production-deployed models. This is an output-side signal.
  - Source: https://www.praetorian.com/blog/exploiting-llm-write-primitives-system-prompt-extraction-when-chat-output-is-locked-down/
  - **aigis takeaway:** An output-side pattern detecting refusal messages that include quoted
    instructions would be valuable, but requires careful scoping to avoid false positives on
    legitimate refusal messages. Deferred to pending.

- **CVE-2026-42208 (LiteLLM SQL Injection, April 2026)**: CVSS 9.3 SQL injection via unsanitized
  Authorization headers. Added to CISA KEV on May 8, 2026. Exploited within 26 hours of disclosure.
  - Source: https://thehackernews.com/2026/04/litellm-cve-2026-42208-sql-injection.html
  - **aigis takeaway:** Existing `sqli_*` patterns provide partial coverage for SQL injection in
    prompt content, but this CVE is in LiteLLM's HTTP handling layer — infrastructure-level, not
    prompt-level. No new pattern needed.

- **CVE-2026-33626 (LMDeploy SSRF, April 2026)**: SSRF exploited within 12.5 hours of disclosure.
  Demonstrates the narrow window between LLM-framework CVE disclosure and active exploitation.
  - Source: (SecurityAffairs advisory, April 2026)
  - **aigis takeaway:** SSRF detection (`exfil_send_to_external`) partially covers prompt-level
    SSRF triggers. Infrastructure-level SSRF is out of scope for prompt-layer firewall.

---

## Candidate Hardenings

1. **`jb_task_masking`** (score 55, input filter) — Bracket-notation placeholder token +
   fill-in-the-blank task instruction. **→ IMPLEMENTED**

2. *(pending)* Output-side refusal quote extraction detector — detect model output that quotes
   internal instructions in a refusal. Requires careful false-positive scoping.

3. *(pending)* Multi-turn escalation detection via conversation-level state — requires
   cross-turn correlator, not single-turn filter. Roadmap item.
