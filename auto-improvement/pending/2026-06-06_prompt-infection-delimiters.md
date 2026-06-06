# Pending: Prompt Infection Structural Delimiter Patterns

- **Title**: Add structural delimiter patterns for self-replicating Prompt Infection payloads
- **Motivation**: The Prompt Infection paper (arxiv:2410.07283, UCL/Stanford, COLM 2025) documents a specific payload format using `[[[`/`]]]` triple-bracket delimiters, section headers like `[NEW ROLE]`, `[ALGORITHM]`, `[TIP]`, and `<USER>`/`</USER>` XML tags to wrap self-replicating payloads with per-hop role assignments. These literal structural signatures are not yet covered by the existing `_SELF_REPLICATION_PATTERNS` (which detect *intent* language rather than *structure*).
- **Research finding**: arxiv:2410.07283 shows >80% ASR against GPT-4o. The payload format is distinctive: non-final agents are instructed to reproduce the entire payload inside `[[[...]]]` delimiters, and a `Data:` field accumulates sensitive data across hops.
- **Proposed change**: Add to `_SELF_REPLICATION_PATTERNS` in `aigis/multi_agent/message_scanner.py`:
  ```python
  re.compile(r"\[\[\[[\s\S]{10,}\]\]\]", _FLAGS)  # triple-bracket delimiter wrapper
  re.compile(r"\[(NEW\s+ROLE|ALGORITHM|TIP|DATA|PAYLOAD)\]", _FLAGS)  # section headers
  ```
- **Why held back**: The triple-bracket pattern requires `re.DOTALL` and spans potentially large content blocks. Need to verify performance on very long messages before shipping. The cycle 6 implementation budget was spent on goal-hijack and trust-bootstrap patterns.
- **Constraint**: Implementation budget (100 LOC) already used this cycle. These are small patterns but should be tested for ReDoS risk first.
- **Suggested next step**: In the next `multi-agent` cycle, add these patterns with a ReDoS regression test. Reference `tests/test_redos_regression.py` for the test pattern.
