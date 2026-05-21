# Research: Jailbreak & System-Prompt Extraction — Third Pass (Domain 3)

**Cycle timestamp:** 2026-05-21T09-07
**Domain:** jailbreak-extraction (#3)
**Prior coverage:**
- 2026-05-08T05-49 — DAN/no-restrictions, grandma exploit, fictional bypass, developer mode, ignore ethics
- 2026-05-10T12-00 — Bad Likert judge, many-shot, affirmative prefill, hypothetical AI, academic bypass
- 2026-05-13T08-30 — Structured extraction (JSON enumeration), sandwich-style verbatim extraction

---

## Findings

1. **Speak Easy: Payload Splitting via Step Enumeration (arxiv:2502.04322, ICML 2025)**
   Source: https://arxiv.org/abs/2502.04322
   "Speak Easy" decomposes a harmful request into numbered innocuous sub-queries where no single
   step triggers safety filters. A chemistry query is split into: "Step 1: What household chemicals
   exist?" → "Step 2: Which combinations are dangerous?" → "Step 3: Describe the reaction." GPT-4o's
   attack success rate increases from 9.2% to 55.5% using this technique; combined with TAP-T
   multilingual translation, ASR exceeds 90%. The technique exploits "single-step myopia" in safety
   classifiers trained to evaluate individual messages in isolation.
   **Aigis takeaway:** A pattern detecting 3+ numbered/labelled steps where dangerous content
   appears in step 3 or later closes the single-turn form of this attack.

2. **M2S: Multi-Turn to Single-Turn Jailbreak Consolidation (arxiv:2503.04856, ACL 2025)**
   Source: https://arxiv.org/abs/2503.04856
   Multi-turn-to-Single-turn (M2S) converts Crescendo-style multi-turn jailbreaks into efficient
   single-turn prompts using three format methods: (1) **Hyphenize** — bullet-pointed turns;
   (2) **Numberize** — numbered turns ("Turn 1: ...\nTurn 2: ..."); (3) **Pythonize** — Python
   list of turn strings. M2S achieves 70.6–95.9% ASR across frontier LLMs, outperforming original
   multi-turn attacks by up to 17.5 percentage points while reducing token usage by >50%. An
   LLM-based input-output filter (Llama-Guard-3-8B) was bypassed at 71.0% vs. 66.1% for the
   original multi-turn form — single-turn consolidations are *harder* to detect than the original.
   **Aigis takeaway:** The "Turn N:" label format is a detectable signal distinct from `jb_many_shot`
   (which targets Human/Assistant role markers). Adding "turn" to the step-enumeration detector
   catches M2S Numberize consolidations.

3. **Adversarial Poetry Jailbreak (arxiv:2511.15304, Nov 2025)**
   Source: https://arxiv.org/abs/2511.15304
   Encoding harmful requests in poetic form (ballad, rap, haiku, limerick, sonnet) achieves
   62% average ASR across 25 frontier LLMs for hand-crafted adversarial poems. An automated
   meta-prompt that converts any MLCommons 1,200 harmful prompts into verse achieves 43% ASR
   with zero manual effort. The Register covered the paper's findings. The creative-format
   framing suppresses safety refusals by exploiting the model's lower-risk register for artistic
   generation. The existing `jb_fictional_bypass` pattern catches some creative framing but
   uses a 100-char bounded window that misses poetry directives where the harmful keyword
   appears deeper in the request.
   **Aigis takeaway:** A dedicated `jb_poetry_harmful_framing` pattern covering rap/poem/ballad/
   haiku/etc. + harmful keyword within ~200 chars specifically closes this gap.

4. **Echo Chamber Multi-Turn Jailbreak (arxiv:2601.05742, NeuralTrust, Jan 2026)**
   Source: https://arxiv.org/abs/2601.05742
   NeuralTrust discovered the Echo Chamber Attack: instead of individual jailbreak tricks, it
   embeds "steering seeds" — harmless-looking hints — into acceptable queries to build a poisoned
   conversational context that progressively nudges the model toward harmful outputs over multiple
   turns. Unlike Crescendo (which escalates directly), Echo Chamber works by conditioning the
   model's semantic associations across turns. Demonstrated against OpenAI and Google models in
   standard black-box settings. NeuralTrust recommends "toxicity accumulation scoring" that tracks
   subtle escalation across turns.
   **Aigis takeaway:** Requires multi-turn state tracking, which is outside the current single-turn
   pattern architecture. Save to pending; the feature would need a new `ConversationRiskTracker`
   class (already sketched in `2026-05-08_crescendo-multiturn-detection.md` pending proposal).

5. **Multilingual Jailbreak via Low-Resource Languages (arxiv:2605.18239, May 2026)**
   Source: https://arxiv.org/abs/2605.18239
   Stellenbosch University (May 18, 2026): multi-turn conversations in low-resource African
   languages (Afrikaans, Kiswahili, isiXhosa, isiZulu) bypass safety mechanisms. Single-turn
   translation attacks are ineffective; multi-turn achieves 52.7%–83.6% harmful response rates
   (Claude 3.5 Haiku to GPT-4o-mini). Human red-teaming raises average ASR from 59.8% to 75.8%.
   Safety training is English-centric; low-resource language variants bypass English-language
   safety rules.
   **Aigis takeaway:** Requires language detection at the input layer, which aigis does not
   currently provide. The attack is in the semantics of the translated content, not the encoding.
   Cannot be caught by regex patterns. Save to pending as a documentation/guide item.

6. **JBFuzz: Fuzzing-Based Jailbreak with 99% ASR (Mar 2026)**
   Source: https://redteams.ai/blog/llm-jailbreaking-2026
   JBFuzz applies software fuzzing to LLM jailbreaking, treating the input space like a binary
   format. It generates mutations of effective jailbreak templates, tests them against the target
   model, and uses feedback to evolve more effective prompts. Average 99% ASR against GPT-4o,
   Gemini 2.0, and DeepSeek-V3; average time-to-jailbreak of 60 seconds with ~7 queries. The
   evolved prompts are highly varied and model-specific — no stable canonical form for rule-based
   detection.
   **Aigis takeaway:** JBFuzz generates unique prompts that resist rule-based detection. No
   implementation candidate this cycle; the defense is model-level safety training, not input
   filtering.

7. **Defensive M2S: Training Guardrails on Compressed Conversations (arxiv:2601.00454, Jan 2026)**
   Source: https://arxiv.org/abs/2601.00454
   The defensive companion to M2S: a guardrail model trained on M2S-compressed multi-turn
   conversations achieves better detection than models trained on original multi-turn data.
   Key insight: the structural formatting of M2S prompts (numbered turns, bulleted turns,
   code-like syntax) is a detectable artifact, not just a semantic escalation. This validates
   the approach of using formatting as a detection signal.
   **Aigis takeaway:** Confirms that structural formatting (step enumeration, turn labels) is
   a reliable detection signal for M2S attacks — validates the `jb_payload_splitting` rule.

8. **X-Teaming Evolutionary M2S Templates (arxiv:2509.08729, Sep 2025)**
   Source: https://arxiv.org/abs/2509.08729
   X-Teaming extends M2S by automatically evolving the most effective single-turn template
   structures. Shows that Numberize and Pythonize are both effective and that the "Turn N:" /
   step-enumeration patterns are stable across evolved variants.
   **Aigis takeaway:** Further confirms that "Turn N:" enumeration is a persistent structural
   feature of M2S attacks.

---

## Candidate Hardenings

1. **`jb_payload_splitting`** (score 45, input filter) — Detect 3+ numbered or turn-labelled
   steps where a dangerous keyword appears in step 3+. Addresses Speak Easy (arxiv:2502.04322,
   55.5% ASR) and M2S Numberize (arxiv:2503.04856, 70.6–95.9% ASR). Resolves pending proposal
   `auto-improvement/pending/2026-05-10_jb-payload-splitting.md`. *(Implement this cycle.)*

2. **`jb_poetry_harmful_framing`** (score 55, input filter) — Detect creative-format directive
   (rap/poem/ballad/haiku etc.) + harmful keyword within ~200 chars. Addresses adversarial
   poetry (arxiv:2511.15304, 62% ASR across 25 LLMs). Resolves pending proposal
   `auto-improvement/pending/2026-05-10_jb-poetry-harmful-framing.md`. *(Implement this cycle.)*

3. **Echo Chamber multi-turn detector** — Requires stateful conversation tracking. Deferred;
   see pending `2026-05-08_crescendo-multiturn-detection.md`.

4. **Multilingual low-resource jailbreak guide** — Requires language detection. Deferred;
   save to pending as documentation guidance.
