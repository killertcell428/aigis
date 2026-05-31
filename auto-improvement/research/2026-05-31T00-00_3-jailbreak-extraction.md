# Research: jailbreak-extraction — 2026-05-31T00-00

## Domain: jailbreak-extraction (index 3, fourth pass)
## Cycle start UTC: 2026-05-31T00-00
## Focus: Special-token injection (MetaBreak), creative-format bypass (poetry), and 2026 jailbreak landscape

Prior cycles covered:
- Cycle 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks (both implemented).
- Cycle 2 (2026-05-10): DIA-I affirmative prefill, Hypothetical unrestricted AI, Academic bypass framing (all implemented).
- Cycle 3 (2026-05-13): Structured JSON extraction (`jb_structured_extraction`), Sandwich verbatim extraction (`jb_sandwich_extraction`) — both implemented; ICE / PHISH deferred (multi-turn only).

This pass targets special-token injection (MetaBreak, arxiv:2510.10271) and the creative-format (poetry/song) bypass technique (arxiv:2511.15304), both of which were deferred or not yet covered.

---

## Findings

- **MetaBreak: Special-Token Injection** (arxiv:2510.10271, Oct 2025): Attackers inject model-level chat-template control tokens (`<|im_start|>`, `<|im_end|>`, `<|begin_of_text|>`, `<|eot_id|>`, `<|endoftext|>`, `[INST]`, `[/INST]`, `<<SYS>>`, `<</SYS>>`) directly into user-supplied text to trick the model into treating injected text as a privileged system or assistant turn. The attack demonstrated four primitives: Response Injection (forging an assistant turn inside user input), Turn Masking (word-by-word construction around platform-added wrappers), Input Segmentation (splitting harmful keywords with special tokens to evade content moderators), and Role Override (injecting `<|im_start|>system` to prepend a new system instruction). Boosted PAP attack success rate by +24.3% and GPTFuzzer by +20.2%. Outperforms PAP and GPTFuzzer by 11.6% and 34.8% when content moderation is deployed.
  - Source: https://arxiv.org/abs/2510.10271
  - **aigis takeaway:** Model chat-template special tokens should never appear in legitimate user input. Their presence is a near-certain signal of a MetaBreak-style attack. A regex covering the most distinctive multi-model token set has extremely low false-positive rate.

- **Creative-Format (Poetry / Song) Jailbreak** (arxiv:2511.15304, Nov 2025): Encoding harmful requests in poetic or musical form achieves 62% average ASR across 25 frontier models including GPT-4o, Claude Sonnet, and Gemini 1.5. The paper tested Google, OpenAI, Anthropic, DeepSeek, xAI, and Meta models. The technique exploits a gap in safety training: models are trained on direct harmful requests but not specifically on poetry-encoded requests. An automated meta-prompt that converts any direct request to a poetry format achieved 43% ASR. This was covered in pass 2's candidate list but deferred because the LOC budget was exhausted.
  - Source: https://arxiv.org/abs/2511.15304
  - **aigis takeaway:** Add `jb_poetry_harmful_framing` — (write/compose/create poem/rap/song/haiku/verse/lyrics) + harmful topic keyword within ~200 chars. Score 60.

- **JBFuzz: Fuzzing-Based Jailbreak Automation** (arxiv:2503.08990, Mar 2025): Applies software fuzzing to automatically generate jailbreak mutations, achieving 99% average ASR across GPT-4o, Gemini 2.0, and DeepSeek-V3 in ~60 seconds and ~7 queries. JBFuzz generates mutations of existing jailbreak seed prompts (DAN, roleplay, fictional framing) and uses model feedback to evolve more effective prompts. Not a single detectable pattern — it generates new permutations of known templates — but it confirms that broader rule coverage reduces the effective surface JBFuzz can exploit.
  - Source: https://arxiv.org/abs/2503.08990
  - **aigis takeaway:** No single new rule; JBFuzz relies on existing jailbreak primitives that are already covered. Broader rule coverage reduces its effective attack surface.

- **Deceptive Delight** (Palo Alto Networks Unit 42, Oct 2024): Embeds a harmful topic among benign ones in a creative narrative request, then asks for elaboration. Achieves 64.6% ASR within 3 interaction turns. The initial-turn signal (asking to connect two benign topics and one harmful topic in a narrative) is partially detectable but high false-positive rate without multi-turn context.
  - Source: https://unit42.paloaltonetworks.com/jailbreak-llms-through-camouflage-distraction/
  - **aigis takeaway:** Multi-turn technique — a single-turn regex would catch too many legitimate creative writing requests. Defer to pending.

- **Autonomous LLM-vs-LLM Jailbreak (Nature Communications 2026)**: Reasoning models achieve 97.14% overall ASR when autonomously jailbreaking other LLMs with no human involvement. Claude showed the lowest ASR (2.86%); DeepSeek-V3 was most vulnerable (90%). Rule-based perimeter defense remains the correct architecture for aigis.
  - Source: https://redteams.ai/blog/llm-jailbreaking-2026
  - **aigis takeaway:** Confirms that surface-area reduction (more rules) is the right defense posture for rule-based systems. No single new pattern.

- **Adaptive Attacks Bypass Documented Defenses** (arXiv, OpenAI/Anthropic/DeepMind joint study, 2025): 12 published defenses were all bypassed with >90% success rate by adaptive attackers. Rule-based filtering has inherent limitations but remains an important first-line defense reducing effective ASR for non-adaptive, automated tooling.
  - Source: https://reddogsecurity.substack.com/p/llm-security-in-2026-a-complete-attack
  - **aigis takeaway:** No single new rule; confirms defense-in-depth posture.

---

## Candidate hardenings

1. **`jb_special_token_injection`** (input, score 70) — Detects MetaBreak-style injection of model chat-template special tokens (`<|im_start|>`, `<|im_end|>`, `<|begin_of_text|>`, `<|eot_id|>`, `<|endoftext|>`, `[INST]`, `[/INST]`, `<<SYS>>`, `<</SYS>>`) in user-provided text. These tokens should never appear in legitimate user input; their presence indicates an attempt to hijack the chat-template role structure. **→ IMPLEMENT**

2. **`jb_poetry_harmful_framing`** (input, score 60) — Detects creative-format bypass: requesting harmful content expressed as a poem, rap, song, haiku, or other creative form. Covers the adversarial poetry jailbreak technique (arxiv:2511.15304; 62% ASR). Pattern requires co-occurrence of creative-format directive + harmful topic keyword. **→ IMPLEMENT**

3. *(pending)* **Deceptive Delight** — Multi-turn narrative co-occurrence attack. Single-turn regex has too many false positives without turn context.

4. *(pending)* **JBFuzz coverage** — No single detectable pattern; requires monitoring of mutation-space coverage.
