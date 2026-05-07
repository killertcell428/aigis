# Research: Prompt Injection — Cycle 0

**Domain:** `prompt-injection`  
**Cycle UTC:** 2026-05-07T14-24  
**Coverage angle:** Indirect prompt injection in the wild + new evasion/spoofing vectors (2026 Q1–Q2)

---

## Key Findings

- **AI-addressee in-the-wild pattern.** Forcepoint (Feb 2026) and Unit 42 (Mar 2026) both documented real payloads triggering on patterns like `"If you are an LLM"` and `"Attention: AI"` embedded in scraped web pages and email threads. These are invisible to human readers but consumed by the LLM processing the document. Google saw a 32% relative increase in malicious indirect injection content between Nov 2025 and Feb 2026.
  - *For aigis:* Adds a new detection surface in RAG/web-scraping pipelines. A new rule targeting "if you are an AI/LLM" constructs closes the gap.
  - Source: https://www.helpnetsecurity.com/2026/04/24/indirect-prompt-injection-in-the-wild/

- **Chat-format delimiter spoofing.** Tool-result injection research (Jan–Mar 2026) shows attackers embedding LLM chat-format delimiters (`<|eot_id|>`, `<|start_header_id|>`, `[/INST]`, `[HUMAN]`) inside JSON fields returned by agent tools. These tokens trick models into treating attacker-controlled content as system or assistant turns.
  - *For aigis:* Existing `ii_hidden_instruction` catches `<|im_start|>system` and `[INST]` but not the closing/companion tokens. A new delimiter-spoof rule covers the gap.
  - Source: https://arxiv.org/abs/2601.04795

- **"HashJack" URL fragment injection.** Microsoft MSRC (Jul 2025) documented attackers appending malicious instructions after `#` in URLs (`https://domain.com/page#IGNORE_INSTRUCTIONS`). Agents that pass raw URLs to LLMs for summarisation ingest the fragment as instructions.
  - *For aigis:* Candidate hardening (see pending). Requires careful regex to avoid false positives on legitimate URL fragments.

- **Unicode tag smuggling (U+E0000–U+E007F).** Aigis `decoders.py` already detects and strips this range (`detect_invisible_tags` / `strip_invisible_tags`). Cisco/AWS 2025 research confirmed this remains the highest-bypass technique vs. commercial guardrails (bypasses Protect AI v2, Azure Prompt Shield).
  - *For aigis:* Already covered. No implementation needed.

- **Emoji-smuggling bypass.** "Emoji and Unicode tag Smuggling" fully bypassed all detection across Protect AI v2 and Azure Prompt Shield (arXiv 2504.11168, Apr 2025). Aigis `enc_emoji_substitution` and emoji-stripping in `decoders.py` already cover this.
  - *For aigis:* Already covered.

- **Many-shot / crescendo multi-turn escalation.** Multi-turn attacks exceeding 70% success vs. single-turn-only defenses. Crescendo starts with benign adjacents and escalates across turns. Hard to detect in a single message without conversation context.
  - *For aigis:* No single-regex rule is feasible per hard constraints; conversational scoring would require context state (pending idea).

- **PoisonedAlign — alignment-data poisoning.** Even a small fraction of poisoned alignment samples makes LLMs 20×+ more susceptible to injection while preserving benchmark performance (AISec 2025). Downstream detection concern only; not detectable at inference.
  - *For aigis:* No runtime rule applicable.

- **Indirect injection success rates.** Large-scale competition (arXiv 2603.15714, Mar 2026) shows frontier LLMs still fail 15–40% of hidden IPI attempts even with hardened system prompts. End-to-end attack chains including retrieval step reach 26% success vs. 2–4% for isolated injections.
  - *For aigis:* Validates importance of RAG/retrieval-layer scanning.

---

## Candidate Hardenings

| Priority | Change | Fits constraints? |
|----------|--------|-------------------|
| **HIGH** | New pattern `ii_ai_addressee`: detect "if you are an AI/LLM/model" addressee constructs in retrieved content | ✅ Implemented this cycle |
| **HIGH** | New pattern `ii_delimiter_spoof`: detect `<\|eot_id\|>`, `<\|start_header_id\|>`, `[/INST]`, `[HUMAN]`, `---END OF USER INPUT---` delimiter spoofing | ✅ Implemented this cycle |
| **MED** | New pattern `ii_url_fragment_inject`: detect `#` fragments containing injection keywords in URLs passed to AI | ⏳ Pending (false-positive risk; see pending/) |
| **LOW** | Conversational crescendo scorer: track topic distance across turns | ⏳ Pending (requires context state, breaking abstraction) |
