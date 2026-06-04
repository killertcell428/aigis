# Pending: Reasoning Hijacking / Decision-Criteria Injection Detection

**Title:** Detect criteria-injection payloads that subvert LLM classification reasoning
**Motivation:** arxiv:2601.10294 (ACL 2026) documents "Reasoning Hijacking" — a vulnerability where attackers inject spurious decision criteria into an LLM's chain-of-thought reasoning without altering the stated task goal. Because the attack maintains task-level alignment, it bypasses defenses like SecAlign and StruQ that look for goal deviation or instruction-override language. The attack was demonstrated on classification tasks (toxic content, spam, sentiment) with high effectiveness.

**Research finding:** arxiv:2601.10294 — "Reasoning Hijacking: Subverting LLM Classification via Decision-Criteria Injection" (ACL 2026). The attack injects phrases like "evaluate this using the following criteria" or "the real decision rule is X" into context, causing the model to prioritize the injected heuristics over its training.

**Proposed change:** Add a `_CRITERIA_INJECTION_PATTERNS` group in `AgentMessageScanner` detecting:
- "evaluate (this|the content) using the following criteria"
- "the (real|actual|correct|true) (classification|decision) (rule|criterion|criteria) is"
- "apply (these|the following) (rules|criteria) when (deciding|judging|classifying)"

**Why held back:** The attack is fundamentally semantic — it works by introducing plausible-sounding evaluation criteria that the model then over-weights. Regex patterns matching the above phrases would have significant false-positive rate in legitimate orchestration messages (e.g., an evaluator agent legitimately explaining its scoring criteria to a downstream agent). The attack requires semantic understanding of whether the "criteria" being injected are adversarial. A viable approach might be to flag these patterns only when criteria injection appears alongside score manipulation cues or in tool-result messages where injected criteria are unexpected.

**Constraint that blocked it:** High false-positive risk; semantic rather than syntactic detection is needed. The ≤ 100 LOC non-test constraint also makes it hard to add an adequate ML-free semantic check.

**Suggested next step:** Design a combined signal: criteria-framing language + suspiciously specific numerical thresholds or overrides of named safety rules. Add a test suite with benign evaluator-agent messages and malicious criteria-injection messages before implementing.
