# Pending: Thinking-Mode Output-Filter Hardening Guide

**Title:** Documentation guide for reasoning-model deployments — raising output-filter thresholds

**Motivation:**
Research (arxiv:2508.10032 "The Cost of Thinking") shows that LLMs in "thinking/reasoning
mode" (chain-of-thought, DeepSeek-R1, Claude extended thinking, Gemini reasoning mode) are
more susceptible to jailbreaks than non-reasoning counterparts. The internal CoT frequently
acknowledges the harmful nature of a query but then proceeds anyway "for educational purposes."
Users deploying reasoning models behind aigis should apply tighter output-filter score thresholds.

**Research finding that led to this idea:**
`auto-improvement/research/2026-05-23T03-06_3-jailbreak-extraction.md` — Thinking-mode
amplification finding.

**Proposed change:**
Add `docs/hardening-reasoning-models.md` explaining:
1. Why reasoning-mode models show higher jailbreak ASR even against identical prompts.
2. Recommended aigis score threshold adjustments: lower the `block_threshold` from 70 to 50
   when the monitored model uses extended thinking or chain-of-thought.
3. How to combine input filtering (aigis detects jailbreak attempts early) with output
   filtering (aigis catches any harmful content that leaked through).
4. Reference: arxiv:2508.10032, promptfoo security database entry for "Thinking Mode
   Jailbreak Amplification".

**Why it was held back:**
- Documentation-only change; no code change required.
- Can be done in any cycle without risk of breaking tests.
- Lower priority than an implementable detection rule.

**Constraint that blocked it:**
No hard constraint — deferred due to lower priority vs. the implementable poetry-framing pattern.

**Suggested next step for human reviewer:**
Draft `docs/hardening-reasoning-models.md` using the structure above. Reference
`docs/hardening-guide.md` for style conventions. This is a low-risk, high-value addition
for teams deploying aigis with reasoning-mode models.
