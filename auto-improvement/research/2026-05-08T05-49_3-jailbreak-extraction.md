# Research: Jailbreak & System Prompt Extraction (Cycle 3)

**Domain:** `jailbreak-extraction` (index 3)
**Cycle start UTC:** 2026-05-08T05-49
**Sources consulted:** arXiv, Palo Alto Unit 42, Anthropic research, VentureBeat, ACL Anthology, OpenReview

---

## Key Findings

- **Bad Likert Judge** (Palo Alto Unit 42, Jan 2025): Multi-turn jailbreak that asks the LLM to act as a judge rating content harmfulness on a Likert scale, then requests example responses at each score level. Achieves 60%+ improvement in attack success rate (ASR) vs. plain prompts; >75 percentage points better in some categories. Targets hate, self-harm, malware generation, and system prompt leakage specifically. Models with content filters reduced this ASR by 89.2%.
  - **aigis takeaway:** The two-step structure (rate on scale → generate examples) is detectable. Pattern can be matched with a two-part regex.
  - Source: https://unit42.paloaltonetworks.com/multi-turn-technique-jailbreaks-llms/

- **Many-Shot Jailbreaking** (Anthropic research 2024, widely replicated through 2025): Embeds dozens to hundreds of faux human/AI dialogue pairs in a single prompt to condition the model into producing harmful content at the final turn. Effectiveness follows a power law. Baseline ASR of 61–86% across Claude 2.0, GPT-3.5, GPT-4, Llama 2 70B, Mistral 7B. Easily detectable by counting dialogue turn markers.
  - **aigis takeaway:** Repeated `Human: … / Assistant: …` patterns (3+ pairs) in a single message are a strong signal.
  - Source: https://www.anthropic.com/research/many-shot-jailbreaking

- **Persona Evolution via Genetic Algorithm** (arXiv 2507.22171, Jul 2025): Automated genetic-algorithm-based crafting of persona prompts reduces refusal rates by 50–70% across multiple LLMs. Existing `jb_evil_roleplay` in aigis already covers the core pattern; evolutionary variants overlap substantially.
  - **aigis takeaway:** Existing coverage is adequate. No new rule needed.

- **BOOST / EOS Token Injection** (OpenReview, 2025): Appending EOS tokens (e.g., `</s>`) to harmful prompts shifts the input closer to the refusal boundary in hidden space, causing the model to respond anyway. Major providers (OpenAI, Anthropic, Qwen) do not filter EOS tokens.
  - **aigis takeaway:** Chat-delimiter token spoofing is already covered by `ii_delimiter_spoof`. EOS-only appending (no surrounding tokens) is near-impossible to distinguish from encoding artifacts without semantic context — out of scope for rule-based detection.

- **MetaBreak / Special Token Manipulation** (arXiv 2510.10271, Oct 2025): Injecting chat-format special tokens (`<|im_end|>`, `[/INST]`, `<|eot_id|>`) into user-supplied text to escape the user turn and inject system-level instructions. Already covered in aigis by `ii_delimiter_spoof` (INDIRECT_INJECTION_PATTERNS).
  - **aigis takeaway:** Existing rule covers the core attack vector. No duplication needed.

- **Encoding Tricks (Leetspeak, Base64, Zero-Width)** (arXiv 2406.08754, Red Team survey 2025): Encoding-based evasion achieves 76.2% ASR against keyword filters. Already covered in aigis by `ENCODING_BYPASS_PATTERNS`.
  - **aigis takeaway:** Existing coverage is adequate.

- **Multi-Turn / Crescendo Escalation** (arXiv 2404.01833, USENIX Security 2025): Gradually escalating dialogue over multiple turns. 70%+ ASR against single-turn-only defenses. Cannot be reliably detected by single-input rule-based filters without conversation-state tracking.
  - **aigis takeaway:** Out of scope for this cycle. Requires stateful conversation analysis — saved to pending.

---

## Candidate Hardenings

1. ✅ **jb_bad_likert_judge** — Two-part regex detecting (rate/score on a Likert/N-scale) + (generate examples for each level). Implemented.
2. ✅ **jb_many_shot** — Regex detecting 3+ consecutive faux Human/Assistant dialogue pairs in a single message. Implemented.
3. ⏳ **Crescendo multi-turn detection** — Requires stateful conversation tracking across turns. Deferred to pending.
