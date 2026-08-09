# Pending: Structural Template Injection Syntactic Variants

**Title:** Extend chat-template injection coverage with STI syntactic variants

**Motivation:**
arxiv:2602.16958 (February 2026) systematically enumerates Structural Template Injection (STI)
syntactic variants achieving 79.76% average attack success rate across seven closed-source
agents (GPT-4o, Qwen, Gemini variants) and identified 70+ vulnerabilities in 942 commercial
agents. The existing `_CHAT_TEMPLATE_INJECTION_PATTERNS` cover the core tokens (`<|user|>`,
`<|im_start|>`, etc.) and fake role-prefix turns, but the STI paper documents additional
variants that may evade the current patterns.

**Research finding that led to this idea:**
"Automating Agent Hijacking via Structural Template Injection" (arxiv:2602.16958, Feb 2026).
The attack constructs three-component injection: (1) deceptive tool-call termination, (2) forged
assistant response, (3) forged user query. Variants include Unicode lookalike role tokens,
mixed-case formatting of role markers, and template tokens specific to newer model families
not currently covered.

**Proposed change:**
Audit the STI paper's full variant inventory against the current `_CHAT_TEMPLATE_INJECTION_PATTERNS`
and add missing syntactic forms. Candidates include:
- `<|tool_end|>`, `<|tool_call_end|>`, `<|/tool_call|>` — tool-frame termination tokens
- `<|start_header_id|>system<|end_header_id|>` — Llama 3.1+ header format
- `[TOOL_RESULTS]`, `[TOOL_CALLS]` — Mistral/Mixtral tool delimiter format
- Unicode lookalikes of `<|user|>` that bypass exact-match filters

**Why it was held back:**
Requires careful study of the full variant inventory from the paper to avoid false positives.
The current patterns were validated against known-safe benign content; extending them with
additional lookalike patterns requires similar validation. This is suitable for a dedicated
cycle with access to the full paper content.

**Which constraint blocked it:**
Time/research constraint in this cycle — the paper's full syntactic variant table was not
retrieved in detail. Adding patterns without validation risks false-positive regressions.

**Suggested next step for human reviewer:**
1. Fetch and read the full PDF of arxiv:2602.16958.
2. Extract the complete syntactic variant table from the paper.
3. For each variant, check whether the existing `_CHAT_TEMPLATE_INJECTION_PATTERNS` already
   covers it.
4. Add patterns for uncovered variants with test cases, keeping each addition ≤ 20 LOC to
   stay within the 100 LOC cycle budget.
