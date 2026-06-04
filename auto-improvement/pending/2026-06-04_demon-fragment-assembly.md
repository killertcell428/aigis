# Pending: DemonAgent Multi-Fragment Backdoor Staging Patterns

**Title:** `demon_fragment_assembly` — Detect DemonAgent-style multi-fragment backdoor staging in inter-agent messages

**Motivation:**
DemonAgent (arxiv:2502.12575, BUPT + NTU, Feb 2025) decomposes a malicious payload into multiple "sub-backdoor fragments" that are individually benign-looking and obfuscated. Each fragment is implanted into a different agent tool across the workflow; fragments are only assembled and executed when all have been collected. This defeats content-based scanners because no single message contains the full payload. Measured attack success rate: ~100%, 0% detection rate against standard safety audits.

**Research finding that led to this idea:**
Research agent analysis in `auto-improvement/research/2026-06-04T01-32_6-multi-agent.md` (Finding 8: DemonAgent).

**Proposed change:**
Add 2 patterns to `aigis/multi_agent/message_scanner.py`:

```python
(
    re.compile(
        r"(store|save|remember|keep|retain|cache)\s+(this\s+)?"
        r"(fragment|piece|part|chunk|segment|component|sub[\s\-]?(routine|task|payload|code))"
        r"\s+(for\s+)?(later|future|subsequent|next\s+step|assembly|combining|merging)",
        _FLAGS,
    ),
    "Fragment staging: instructs agent to store a fragment for later assembly (DemonAgent-style backdoor staging)",
    "injection_relay",
),
(
    re.compile(
        r"(combine|assemble|merge|concatenate|join)\s+(the\s+)?"
        r"(stored|saved|cached|previously\s+(provided|given|sent|received))\s+"
        r"(fragments?|pieces?|parts?|chunks?|segments?|components?)",
        _FLAGS,
    ),
    "Fragment assembly: instructs combining previously stored fragments (DemonAgent-style backdoor execution)",
    "injection_relay",
),
```

**Why it was held back:**
Moderate false-positive risk. Agent workflows that process documents or code incrementally may legitimately use phrases like "store this component for later processing" or "combine the saved pieces." The pattern needs context-aware disambiguation — ideally distinguishing between data processing (benign) and code fragment assembly (malicious) — which requires more analysis than was available in this cycle.

**Which constraint blocked it:**
"Do not add features that would introduce high false-positive risk without sufficient test coverage." Also, the cycle's non-test LOC budget was partly consumed by `_TASK_INJECTION_PATTERNS`.

**Suggested next step:**
1. Add a `dangerous` qualifier to the staging pattern — require that the fragment be described as "code," "payload," "script," or "executable," not generic "data" or "document piece."
2. Consider restricting to `message_type == "tool_result"` where fragment assembly instructions are most suspicious.
3. Design 8+ true-positive and 4+ true-negative test cases, then implement with a dedicated test class.
