# Research: Evasion & Obfuscation — Third Pass (Domain 7)

**Cycle timestamp:** 2026-05-16T03-08
**Domain:** evasion-obfuscation (#7)
**Prior coverage:**
- 2026-05-09T00-15 — BIDI override, morse code, leetspeak
- 2026-05-11T12-15 — Unicode Tag Block ASCII Smuggling, Fullwidth Latin

---

## Findings

1. **FlipAttack: Jailbreak LLMs via Flipping (ICML 2025, arxiv:2410.02832)**
   Source: https://arxiv.org/html/2410.02832v1 ;
   https://www.keysight.com/blogs/en/tech/nwvs/2025/05/20/prompt-injection-techniques-jailbreaking-large-language-models-via-flipattack ;
   https://icml.cc/virtual/2025/poster/45738
   FlipAttack exploits the left-to-right processing bias of LLMs by reversing the harmful
   payload at the character or word level and prepending a "decode instruction" that tells the
   LLM to unscramble it. Three flipping modes: Flip Characters in Word (FCW), Flip Complete
   Sentence (FCS), Flip Words Order (FWO). Reversed text has a perplexity of ~810, so guardrail
   classifiers that rely on semantic scoring fail to recognize the payload. The attack achieves
   ~98% ASR against GPT-4o and ~98% bypass rate against five deployed guardrail models in a
   single query. Accepted at ICML 2025; included in Keysight ATI-2025-08 StrikePack as
   strikes flipattack_fcs, flipattack_fcw, flipattack_fwo.
   **Aigis takeaway:** The decode instruction ("read backwards", "flip each word", "characters
   are reversed") is the reliable detection signal — the reversed payload alone looks like
   noise, but the decode instruction is explicitly readable. A DetectionPattern targeting
   these instructions can flag FlipAttack payloads. *(Implemented this cycle.)*

2. **PUZZLED: Jailbreaking LLMs through Word-Based Puzzles (arxiv:2508.01306, Aug 2025)**
   Source: https://arxiv.org/abs/2508.01306
   PUZZLED masks harmful keywords in word-puzzle formats (word search grids, anagram challenges,
   crossword clues) and instructs the LLM to solve the puzzle to reveal and then act on the
   reconstructed harmful phrase. Achieves 88.8% average ASR across five state-of-the-art LLMs,
   with 96.5% on GPT-4.1 and 92.3% on Claude 3.7 Sonnet. The attack exploits the LLM's
   in-context reasoning ability to decode the puzzle while bypassing guardrails that see only
   the surface-level puzzle presentation.
   **Aigis takeaway:** "Solve this anagram:", "word search puzzle:", and "find the hidden word"
   directives before a scrambled payload are detectable signals. However, these phrases also
   appear in legitimate educational/puzzle contexts. Deferred to pending for false-positive tuning.

3. **Diacritics / Zalgo Text Obfuscation — Empirical Results (arxiv:2504.11168, ACL LLMSEC 2025)**
   Source: https://arxiv.org/html/2504.11168v3 ;
   https://aclanthology.org/2025.llmsec-1.8/
   The most comprehensive empirical study of evasion attacks against deployed LLM guardrail
   systems tested eight obfuscation classes against six production systems (Azure Prompt Shield,
   Meta Prompt Guard, Protect AI v1/v2, NeMo Guard, Vijil). Diacritics (Zalgo-style combining
   marks) achieved 44–76% ASR across datasets. Upside-Down text achieved 100% ASR for jailbreaks
   and 63.54% for prompt injections. The paper was the primary source for the Tag Block and
   Fullwidth findings in prior cycles; this cycle covers the diacritics class.
   **Aigis takeaway:** A regex detecting 4+ consecutive combining diacritical marks (U+0300–U+036F)
   catches Zalgo obfuscation with near-zero false-positive rate in AI prompt contexts. Legitimate
   text never exceeds 2 stacked combining marks. *(Implemented this cycle.)*

4. **Bypassing Prompt Injection Detectors through Evasive Injections (arxiv:2602.00750, Jan 2026)**
   Source: https://arxiv.org/html/2602.00750v1
   Evaluates GCG (Greedy Coordinate Gradient) adversarial suffix generation as an evasion method
   against prompt injection detectors. Generates universal suffixes that cause injected inputs to
   evade detection across multiple probe systems, achieving up to 93.91% and 99.63% ASR on Phi-3
   and Llama-3 respectively. The attack is model-specific (requires access to model weights for
   gradient computation) but the generated suffixes transfer to black-box systems.
   **Aigis takeaway:** GCG-generated adversarial suffixes are not detectable by regex patterns
   (the suffix looks like token-level gibberish). This is a theoretical attack class for aigis
   but demonstrates that adversarial perturbation of inputs is a growing threat beyond
   Unicode/encoding tricks. Relevant as a pending idea for a future "anomalous suffix" detector
   based on perplexity or entropy heuristics.

5. **ARGUS: Defending LLM Agents Against Context-Aware Prompt Injection (arxiv:2605.03378, 2026)**
   Source: https://arxiv.org/html/2605.03378
   A defense system for LLM agents that tracks the "context" from which each instruction arrives
   and flags when an instruction claims higher authority than its source context would justify.
   The attack model focuses on indirect prompt injection via retrieved tool outputs and documents.
   Most evasion attempts analyzed rely on plausible-looking authority claims ("this message comes
   from the system orchestrator") rather than encoding obfuscation.
   **Aigis takeaway:** The authority-claim evasion is covered by aigis's existing SAFETY_SPOOF_PATTERNS
   from cycle 6. The context-tracking defense model is architecturally beyond aigis's scope
   (stateful; requires tracking instruction provenance across turns).

6. **Reverse CAPTCHA: Invisible Unicode Instruction Injection (arxiv:2603.00164, Mar 2026)**
   Source: https://arxiv.org/html/2603.00164v1
   Tests whether LLMs follow invisible Unicode-encoded instructions embedded in otherwise
   normal-looking text. The attack embeds instructions using Unicode tag block characters
   (U+E0000–U+E007F) — already covered by aigis's `enc_tag_block_ascii` and
   `te_unicode_tag_smuggling` patterns — but evaluates LLM compliance rate and detection
   bypass rate empirically against current production systems.
   **Aigis takeaway:** Confirms the existing tag block patterns are targeting the right attack
   class. No new rule needed; reinforces prior cycle coverage.

7. **Steganographic Jailbreak: StegoAttack (arxiv:2505.16765, May 2025)**
   Source: https://arxiv.org/abs/2505.16765
   StegoAttack embeds harmful queries within benign, semantically coherent paragraphs using
   text steganography (LSB-style linguistic encoding). Achieves 95.50% average ASR across
   four LLMs, outperforming AutoDAN and Cipher-based approaches. The harmful content is
   statistically indistinguishable from normal text at the pattern level.
   **Aigis takeaway:** Not detectable by regex. The pending TrojanStego entry
   (2026-05-13_trojanstego-linguistic-steganography.md) covers this class. Confirms that
   statistical steganography is out of scope for aigis's rule-based architecture.

8. **Upside-Down Text Unicode Flipping (Referenced in arxiv:2504.11168)**
   Source: https://arxiv.org/html/2504.11168v3
   Upside-down text uses Unicode characters from IPA Extensions (U+0250–U+02AF) and other
   blocks to display Latin letters in a visually flipped orientation. For example, 'a' → 'ɐ',
   'n' → 'u', 'i' → 'ᵢ'. Achieved 100% ASR for jailbreaks and 63.54% for prompt injection
   detection evasion in the arxiv:2504.11168 benchmark. The specific Unicode characters used
   are from legitimate phonetic blocks, so false-positive risk in AI prompt contexts is moderate
   (IPA characters appear in linguistics discussions).
   **Aigis takeaway:** A targeted detection of IPA-flip character pairs (ɐ, ɹ, ǝ, ɯ, ʇ, ʌ, ʍ)
   combined with keyword context would be more precise than blocking all IPA characters.
   Deferred for further FPR analysis.

---

## Candidate Hardenings

1. **`enc_text_reversal` detection pattern** (score 40) — Detect "read backwards", "flip each
   word", "characters are reversed" decode instructions that accompany FlipAttack payloads.
   ICML 2025, ~98% ASR on GPT-4o. Very low FPR; these phrases have almost no legitimate use
   in AI prompt contexts. *(Implemented this cycle.)*

2. **`enc_zalgo_diacritics` detection pattern** (score 45) — Detect 4+ consecutive combining
   diacritical marks (U+0300–U+036F). Catches Zalgo-style obfuscation. arxiv:2504.11168,
   44–76% ASR against production guardrails. Near-zero FPR in AI prompts. *(Implemented this
   cycle.)*

3. **`enc_word_puzzle_instruction` detection pattern** — Detect "anagram:", "solve this word
   search", "unscramble these letters" decode instructions. arxiv:2508.01306 (PUZZLED), 88.8%
   average ASR. Moderate FPR in educational contexts. Deferred to pending for false-positive
   tuning.

4. **`enc_upside_down_text` detection pattern** — Detect IPA-flip characters (ɐ, ɹ, ǝ, ɯ, ʇ, ʌ)
   combined with keyword proximity. arxiv:2504.11168, 100% ASR for jailbreaks. Needs FPR
   analysis against linguistics/phonetics text. Deferred to pending.

5. **GCG adversarial suffix heuristic** — Flag inputs with anomalously high character-level
   entropy or perplexity in a suffix region. arxiv:2602.00750, up to 99.63% ASR against
   detector probes. Not implementable as a regex; requires a chars-per-token or entropy
   heuristic. The existing pending idea `2026-05-09_cpt-chars-per-token-heuristic.md` covers
   this class.
