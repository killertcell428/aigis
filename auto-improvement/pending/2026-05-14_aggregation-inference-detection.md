# Pending: Aggregation inference detection

**Title:** Detect requests to assemble low-sensitivity data fragments into a sensitive composite

**Motivation:**
The SoK on Trust-Authorization Mismatch (arxiv:2512.06914, Dec 2025) identifies "aggregation inference" as a root cause of data exposure in multi-agent systems: individually harmless data items (name, employer, city, role) can be assembled into a PII composite that is sensitive as a whole even though no single field is. An orchestrating agent could be instructed to collect several low-sensitivity fields from different sub-agents and then combine them. The instruction itself may not look like a data exfiltration request.

**Which research finding led to this idea:**
SoK: Trust-Authorization Mismatch (arxiv:2512.06914) — Section 2.3, aggregation inference as a structural root cause of authorization failures.

**Proposed change:**
Add logic to `scan_conversation` in `AgentMessageScanner` to track whether a multi-message sequence has progressively gathered multiple categories of personal data (name, location, email, role, ID, financial) and then bundled them together. Alternatively, add a single-message pattern that detects explicit "combine / aggregate / collect all of: [list of fields including PII types]".

**Why it was held back:**
This requires semantic understanding of what counts as a PII field category across multiple message turns. A purely regex-based approach would require enumerating hundreds of field names. The conversation-level tracking would add meaningful complexity to `scan_conversation` and would likely generate false positives on legitimate data aggregation tasks (e.g., database JOIN operations). This is a pattern that is better suited to an NLP-based classifier or a dedicated PII detector layer (like the `pii` scanner already in aigis), not a regex rule.

**Which constraint blocked it:**
The "zero-runtime-dependency, rule-based" constraint and the "Keep total non-test diff ≤ 100 LOC" limit. A proper implementation would require either an external NLP dependency or a substantial new class (~200+ LOC).

**Suggested next step for the human reviewer:**
Consider extending the existing PII scanner (`aigis/scanner.py` or `aigis/aep/`) to add a conversation-level aggregation check that fires when 3+ distinct PII categories appear across a 5-message window. This would fit naturally into the existing scanner architecture and would not require a new runtime dependency.
