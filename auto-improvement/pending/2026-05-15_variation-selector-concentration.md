# Pending: Variation Selector Concentration Heuristic

**Title:** `enc_variation_selector_density` detection pattern

**Motivation:**
arxiv:2510.05025 (Oct 2025) showed that adversarially optimized sequences of Unicode variation
selectors (U+FE00–U+FE0F, VS-1 through VS-16) appended as invisible suffixes to prompts achieve
high jailbreak success rates against GPT-4, Claude, Llama, and Gemini. The attack works because
guardrail classifiers strip variation selectors before classification (treating them as formatting
noise), while the adversarial bit pattern reaches the downstream LLM's tokenizer intact.

Additionally, the arxiv:2504.11168 benchmark found that variation selector / emoji smuggling
achieved 100% ASR against Protect AI v2 and Azure Prompt Shield — the highest of any class.

**Which research finding led to this idea:**
- arxiv:2510.05025 — "Imperceptible Jailbreaking against Large Language Models"
- arxiv:2504.11168 — "Bypassing LLM Guardrails: An Empirical Analysis"
- Repello AI blog — "Emoji Prompt Injection: Why Your LLM's Guardrails Are Blind to It"

**Proposed change:**
Add a `DetectionPattern` that detects an unusual concentration of Unicode Variation Selectors
(U+FE00–U+FE0F) in a short span of text. The rule would flag inputs where a stretch of N
characters contains more than K variation selectors that are not preceded by a valid base
character + single VS pair (i.e., not a legitimate emoji glyph selector).

Candidate regex approach:
- Detect 3+ consecutive VS characters: `[︀-️]{3,}` (simple threshold)
- Or: detect VS characters not following a base CJK/emoji character (more precise, harder)

**Why it was held back:**
False-positive rate. Unicode variation selectors U+FE0F (VS-16) and U+FE0E (VS-15) are
routinely used in emoji: VS-16 requests the emoji presentation of a character, VS-15 requests
the text presentation. In emoji-rich text, VS-16 appears legitimately after every emoji base
character. The simple threshold `[︀-️]{3,}` would fire on any message containing
3+ emoji with explicit VS-16 selectors.

Distinguishing adversarial VS sequences from legitimate emoji glyph selectors requires
grapheme cluster analysis (parse into grapheme clusters; check if each VS follows a valid
base character and there is at most one VS per cluster). This is not implementable as a
pure regex DetectionPattern.

**Which constraint blocked it:**
"Zero runtime dependency" + "pure regex DetectionPattern" — grapheme cluster analysis
requires either the `regex` library (extended Unicode support) or the `unicodedata` module's
`category()` function used in a non-regex scanner. Both require code changes beyond the
current `DetectionPattern` dataclass architecture.

**Suggested next step for human reviewer:**
Consider adding a new scanner hook (separate from `DetectionPattern`) that runs grapheme
cluster analysis on inputs and contributes to the risk score. This would be the appropriate
home for variation selector density detection, CPT filtering, and other heuristics that
cannot be expressed as a single compiled regex.
