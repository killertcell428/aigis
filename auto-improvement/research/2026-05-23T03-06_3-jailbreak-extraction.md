# Research: jailbreak-extraction — 2026-05-23T03-06

## Domain: jailbreak-extraction (index 3, fourth pass)
## Cycle start UTC: 2026-05-23T03-06
## Focus: Creative-format (poetry/song) jailbreak; self-jailbreaking; multilingual bypass

Prior cycles covered:
- Cycle 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks
- Cycle 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing
- Cycle 3 (2026-05-13): Structured JSON extraction, Sandwich-style verbatim extraction

This pass focuses on the adversarial poetry attack (deferred from cycle 2), new self-jailbreaking
research (arxiv:2601.02670), and a new multilingual low-resource language bypass paper (arxiv:2605.18239).

---

## Findings

- **Adversarial Poetry as a Universal Jailbreak (arxiv:2511.15304, November 2025)**: Framing
  harmful requests as poetry, rap, ballad, song, haiku, or verse achieves an average 62% attack
  success rate (ASR) across 25 frontier closed- and open-weight models, with some providers
  exceeding 90%. Converting 1,200 MLCommons harmful prompts into verse via a standardised
  meta-prompt produced ASRs up to 18× higher than their prose baselines. The attack succeeds
  because models perceive the input primarily as a creative-writing task and deprioritise
  safety alignment. Coverage: CBRN, manipulation, cyber-offence, and loss-of-control domains.
  Paper by Sapienza University of Rome, Sant'Anna School of Advanced Studies, and Dexai.
  - Source: https://arxiv.org/abs/2511.15304
  - **aigis takeaway:** The (write/compose/create/pen) + (poem/rap/song/haiku/verse/ballad) +
    (harmful topic within ~200 chars) three-part structure is detectable in a single-turn filter
    with a low false-positive rate, because legitimate creative requests rarely couple a poetry
    directive with dangerous synthesis keywords. **→ IMPLEMENTED as `jb_poetry_harmful_framing`**

- **SLIP Self-Jailbreaking via Lexical Insertion (arxiv:2601.02670, January 2026)**: Amazon/NYU
  researchers show that an aligned LLM can guide its own compromise. SLIP casts jailbreaking
  as breadth-first tree search over multi-turn dialogues, incrementally inserting missing
  content words from the attack goal into benign prompts. Achieves 90–100% ASR (average 94.7%)
  across 11 tested models (AdvBench / HarmBench) with no external red-team LLM. However,
  SLIP is a multi-turn, stateful technique — individual turns contain only benign-looking
  incremental insertions and are not individually detectable by a single-turn regex filter.
  - Source: https://arxiv.org/abs/2601.02670
  - **aigis takeaway:** Out of scope for single-turn detection. Broader rule coverage (reducing
    the per-turn surface) remains the correct contribution from a rule-based system. Document
    in pending for a future cross-session correlator heuristic.

- **Multilingual Low-Resource Language Jailbreak (arxiv:2605.18239, May 2026)**: Multi-turn
  conversations using low-resource African languages (Afrikaans, Kiswahili, isiXhosa, isiZulu)
  achieve harmful response rates of 52.7% (Claude 3.5 Haiku) to 83.6% (GPT-4o-mini). Simple
  single-turn translation attacks no longer reliably bypass modern guardrails; the vulnerability
  lies in the multi-turn escalation. DeepSeek-V3 and GPT-4o-mini were most vulnerable.
  - Source: https://arxiv.org/abs/2605.18239
  - **aigis takeaway:** Single-turn low-resource-language detection is already partially
    addressed by ENCODING_BYPASS_PATTERNS. Multi-turn escalation in non-English is out of scope
    for single-turn rule-based detection. No new pattern this cycle.

- **JULI Self-Jailbreaking via BiasNet (arxiv:2505.11790, May 2025)**: Manipulates per-token
  log probabilities via a tiny plug-in BiasNet block under a black-box API setting (top-5
  logits only). Outperforms prior state-of-the-art on Gemini-2.5-Pro. Requires access to
  token-level log probabilities — not a prompt-surface attack and not detectable by input
  content filters. JULI targets the inference layer, not the prompt.
  - Source: https://arxiv.org/abs/2505.11790
  - **aigis takeaway:** Infrastructure-level concern (token-probability API access). No
    regex pattern applicable. Noted for documentation / advisory.

- **Thinking Mode Amplification (arxiv:2508.10032)**: LLMs in "thinking/reasoning mode"
  show higher susceptibility to jailbreaks compared to non-reasoning mode. The internal
  chain-of-thought frequently acknowledges harm but then proceeds "for educational purposes."
  Not a new attack vector per se, but a signal amplifier for all existing jailbreak techniques.
  - Source: https://arxiv.org/html/2508.10032
  - **aigis takeaway:** Existing aigis output-filter patterns are more important when the
    monitored model operates in reasoning/thinking mode. No new input pattern needed, but
    users deploying reasoning models should increase aigis output-filter score thresholds.

- **Adversarial Tales / Interpretability Agenda (arxiv:2601.08837, January 2026)**: Follow-up
  to the adversarial poetry paper, extending the framing to short prose "tales" and establishing
  an interpretability research agenda. Prose-tale framing achieved lower ASR than verse (~35%
  vs 62% average), confirming that poetic meter and rhyme constraints suppress safety refusals
  more effectively than narrative prose.
  - Source: https://arxiv.org/abs/2601.08837
  - **aigis takeaway:** Prose-tale framing is partially covered by `jb_fictional_bypass`.
    Poetry/verse form remains the higher-ASR, more distinctive signal.

---

## Candidate hardenings

1. **`jb_poetry_harmful_framing`** (input, score 60) — Creative-format directive (write/compose/
   create + poem/rap/song/haiku/verse/ballad/sonnet/limerick/ode) + harmful topic keyword within
   200 chars (synthesis routes, weapons, malware, network intrusion). Based on arxiv:2511.15304
   (62% ASR, 25 models). **→ IMPLEMENTED this cycle**

2. *(pending)* SLIP cross-session lexical insertion — multi-turn stateful detection, out of
   scope for single-turn filter. Candidate for a future cross-session correlator heuristic.

3. *(pending)* Thinking-mode output-filter guidance — document recommended score threshold
   increases for reasoning-model deployments. Candidate for `docs/` hardening guide.
