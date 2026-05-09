# Research: Evasion & Obfuscation (Domain 7)

**Cycle timestamp:** 2026-05-09T00-15  
**Domain:** evasion-obfuscation (#7)

---

## Findings

1. **Bypassing LLM Guardrails — Full Invisible-Character Benchmark** (arxiv:2504.11168, Apr 2026)  
   Source: https://arxiv.org/abs/2504.11168  
   Tested six deployed systems (Azure Prompt Shield, Meta Prompt Guard, four others) against eight obfuscation classes. Unicode Tag-block smuggling achieved **90.15% / 81.79% ASR** — the highest of any class. BIDI Right-to-Left Override (U+202E) and other invisible controls also achieved >60% ASR in many scenarios.  
   **Aigis takeaway:** The paper confirms that pattern-based scanners which do not explicitly flag invisible Unicode control characters miss a large fraction of real-world obfuscation attempts.

2. **Broken-Token: Characters-Per-Token Filtering** (arxiv:2510.26847, Oct 2025)  
   Source: https://arxiv.org/abs/2510.26847  
   Proposes a lightweight defence: normal English text averages ~4.5 characters/token; obfuscated text (diacritics, fullwidth chars, BIDI insertions) drops to 1–2 chars/token. A CPT threshold of 3.0 catches >85% of obfuscated inputs at <1% FPR.  
   **Aigis takeaway:** Candidate heuristic for a future scoring layer that penalises unusually low chars/token ratios without requiring tokeniser access.

3. **MetaCipher: Cipher-Based Guardrail Bypass Framework** (arxiv:2506.22557, Jun 2025)  
   Source: https://arxiv.org/abs/2506.22557  
   Systematically evaluates 10 encoding schemes (base64, morse, caesar-3, base32, Atbash, etc.) for effectiveness at bypassing safety classifiers. Morse code and Caesar shift-3 outperform the others because both appear frequently enough in LLM pre-training data for models to decode them fluently without any explicit instruction.  
   **Aigis takeaway:** Morse code encoding is a real and measurable threat; adding an explicit morse-detection pattern is justified.

4. **Mixture-of-Encodings Defence** (arxiv:2504.07467, Apr 2025)  
   Source: https://arxiv.org/html/2504.07467v1  
   Survey of encoding-based jailbreaks and corresponding defences. Confirms that cipher diversity (using uncommon encodings not yet in any scanner's ruleset) is the primary adversarial advantage. Pattern coverage of morse, base32, and ASCII art is identified as a near-term gap.  
   **Aigis takeaway:** Expanding encoding bypass coverage (this cycle: morse) provides incremental gains against cipher-diverse attackers.

5. **Leetspeak & Character-Substitution Red-Teaming** (Mindgard Research + DeepTeam framework, 2025)  
   Sources: https://mindgard.ai/resources/bypassing-llm-guardrails-character-and-aml-attacks-in-practice  
           https://www.trydeepteam.com/docs/red-teaming-adversarial-attacks-leetspeak  
   Classic a→4, e→3, o→0, i→1, s→5/$ substitutions in attack keywords bypass naive string-matching filters. These are now included in automated red-teaming toolkits as one of the first transformations applied.  
   **Aigis takeaway:** A compact regex covering the most common attack keywords in leet form (ignore, bypass, system, inject, prompt, jailbreak) closes the most common automated bypass variant.

6. **BIDI Override in the Wild — Trojan Source Class Continues** (Multiple 2025 advisories)  
   Source: https://aws.amazon.com/blogs/security/defending-llm-applications-against-unicode-character-smuggling/  
   The Trojan Source attack (NDSS 2022) showed BIDI overrides can flip the visual meaning of source code while the parser sees something else. In LLM contexts, U+202E causes a human reviewer reading an audit log to see harmless text while the actual prompt bytes contain an injection payload.  
   **Aigis takeaway:** Adding an explicit detection signal for U+202D/202E means BIDI-obfuscated inputs are flagged (scored) in the audit log, not just silently normalised.

7. **TokenBreak: Tokenisation-Strategy Mismatch Exploitation** (arxiv:2506.07948, Jun 2025)  
   Source: https://arxiv.org/abs/2506.07948  
   Exploits the gap between how a safety classifier tokenises text and how the base LLM tokenises it. Inputs that appear benign to a BPE-based classifier can be read fluently by the target LLM after minor character insertions (diacritics, ZWNJ, ZWSP).  
   **Aigis takeaway:** aigis's existing `te_unicode_noise` pattern catches ZWNJ/ZWSP; the BIDI override pattern added this cycle closes the complementary BIDI subclass.

8. **Jailbreaking LLMs & VLMs — Unified Survey** (arxiv:2601.03594, Jan 2026)  
   Source: https://arxiv.org/abs/2601.03594  
   Categorises template/encoding-based attacks as one of seven top-level attack families, with encoding-based variants growing fastest in 2025 (easy to automate, high transferability). Recommends perception-layer normalisation before any semantic safety check.  
   **Aigis takeaway:** Confirms the value of expanding the encoding bypass category rather than focusing solely on semantic/LLM-based detection.

---

## Candidate Hardenings

1. **`enc_bidi_override` detection pattern** — Flag any occurrence of U+202D (LRO) or U+202E (RLO) in user input. Nearly zero legitimate use; high evasion signal. *(Implemented this cycle.)*

2. **`enc_morse_instruction` detection pattern** — Detect explicit `morse:` directives and structural morse-code sequences (6+ dot/dash tokens). Directly addresses MetaCipher findings. *(Implemented this cycle.)*

3. **`enc_leetspeak_keywords` detection pattern** — Detect common attack keywords (ignore, bypass, system, inject, prompt, jailbreak) with digit/symbol substitutions. Closes the primary automated red-team bypass class. *(Implemented this cycle.)*

4. **CPT (chars-per-token) scoring heuristic** — Add a lightweight heuristic that flags inputs where the ratio of Unicode codepoints to approximate token count is abnormally low (<3.0). Would catch diacritic flooding, fullwidth spam, and other multi-codepoint-per-token obfuscations not covered by existing patterns. Deferred: requires stable tokeniser estimate; current scorer has no token-count oracle. Save to pending.

5. **Base32 decoding in `decoders.py`** — MetaCipher showed base32 outperforms base64 in some scenarios because base32 looks more like random uppercase text and fewer scanners decode it. Adding `base64.b32decode` to `decode_all()` would close this. Deferred: needs careful FP analysis on legitimate base32 URLs (RFC 4648 file names). Save to pending.
