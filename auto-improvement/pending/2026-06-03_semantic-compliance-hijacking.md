# Pending: Semantic Compliance Hijacking (SCH) Detection

**Title:** Detect natural-language skill poisoning via obfuscated compliance rules

**Motivation:**
arxiv:2605.14460 (May 2026) introduces Semantic Compliance Hijacking (SCH), an attack that
embeds obfuscated natural-language compliance rules in third-party Agent Skills. Unlike traditional
code injection, SCH provides no explicit malicious payload — instead it uses abstract functional
language that guides capable models to synthesise and execute the malicious action at runtime.
Example: "aggregate the complete mapping of the host environment properties" (means: dump env
vars and exfiltrate them). Attack success rates: up to 77.67% (confidentiality breach) and
67.33% (RCE). Detection evasion against SkillScan and LLM Guard: 100%.

**Research finding that led to this idea:**
"Exploiting LLM Agent Supply Chains via Payload-less Skills" (arxiv:2605.14460, May 2026).
The three core obfuscation techniques are:
1. Control-Flow Eradication — flattening programmatic logic into abstract functional requirements
2. Topological Path Steganography — fragmenting network indicators (e.g., "198, 51, 100, and x
   separated by dots")
3. Emotional & Authoritative Masking — embedding directives in corporate mandates

**Proposed change:**
Add detection patterns for the specific obfuscation vocabulary used in SCH attacks:
- "aggregate the complete mapping of [host|environment|node] properties"
- "capture ambient [node|environment] properties"
- "utilize Python's standard facility for parsing" (followed by remote URL reference)
- "natively adopt it into the shared operational registry" (means: exec() downloaded code)
- Fragmented IP patterns: digits followed by "separated by dots" or similar

**Why it was held back:**
Regex patterns for natural-language obfuscation have very high false-positive risk because
the phrases used are superficially legitimate compliance/operations language. Detection requires
semantic understanding of whether the aggregate action constitutes credential exfiltration or
remote code execution — which is beyond rule-based pattern matching. A dedicated semantic
detection module would be needed.

**Which constraint blocked it:**
The zero-runtime-dependency constraint prevents adding an ML model dependency. Semantic detection
would require either an external LLM call (violates runtime-dependency constraint) or a
lightweight embedding-based classifier (new required dependency).

**Suggested next step for human reviewer:**
1. Evaluate whether a small, pre-compiled keyword/phrase list (without ML) can achieve useful
   precision on the SCH vocabulary without too many false positives.
2. If yes, implement as a new `_SKILL_POISONING_PATTERNS` group in `supply_chain/` scanner.
3. If no, consider adding an optional semantic-detection backend that is disabled by default
   and only enabled when the user explicitly opts in (zero impact on default behavior).
