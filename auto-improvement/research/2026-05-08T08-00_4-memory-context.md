# Research: Memory Context Attacks — Cycle 4 (2026-05-08T08-00)

Domain: `memory-context` — Memory poisoning, context manipulation, long-context attacks, RAG poisoning

## Findings

- **MCFA — Memory Control Flow Attacks (arxiv:2603.15125, Mar 2026)**
  Xu et al. show that retrieved memory entries can dominate an agent's tool-selection logic: a poisoned memory entry forces the agent to call an unintended tool (e.g. `send_email`, `exfiltrate_file`) in contradiction to the user's actual instruction. Tested on GPT-5 mini, Claude Sonnet 4.5, and Gemini 2.5 Flash; >90% of trials were vulnerable.
  **aigis takeaway**: Add a memory scanner pattern that fires when a memory entry contains "use the X tool / call X / invoke X tool" phrasing not in the system-declared tool plan.

- **AgentLAB — Long-Horizon Attack Benchmark (arxiv:2602.16901, Feb 2026)**
  Five attack classes (intent hijacking, tool chaining, task injection, objective drifting, memory poisoning) distribute adversarial intent across multiple turns so no single turn triggers filters. GPT-5.1 showed ~70% average ASR across 644 test cases. The "objective drifting" class is not yet detected by aigis patterns.
  **aigis takeaway**: Add a memory-poisoning pattern for messages that attempt to substitute the user's stated goal with an attacker-controlled "new objective/goal/mission".

- **CorruptRAG — Single-Document RAG Poisoning (arxiv:2504.03957, Apr 2026)**
  Zhang et al. show that a single carefully crafted poisoned document (styled to look like legitimate knowledge) can dominate retrieval for target queries and produce attacker-controlled answers. The CorruptRAG-AK variant uses auxiliary LLM output that *looks* authoritative.
  **aigis takeaway**: Reinforce the RAG filter to detect documents that use "authoritative source" framing combined with instruction overrides. Also: add scan for adversarial suffixes/prefixes used in poisoning corpus injection.

- **RAG Poisoning Benchmark — 13 Attacks × 7 Defenses (arxiv:2505.18543, May 2025/2026)**
  All existing defenses break against agentic, multimodal, and multi-turn RAG. No tested defense generalizes. Key finding: adversarial docs inserted into a sequential RAG pipeline survive all defenses in expanded-dataset conditions.
  **aigis takeaway**: Chunk-provenance is the most reliable defense layer; aigis should document this approach in the RAG filter.

- **CVE-2026-21520 (ShareLeak, Jan 2026 / Apr 2026 disclosure)**
  Copilot Studio agents trusted user form fields as context; injected payload directed agents to silently query SharePoint and exfiltrate contents via Outlook to an attacker domain. CVSS 7.5. The injection was through `send|email|forward|exfiltrate` + object noun patterns.
  **aigis takeaway**: The form-field exfiltration pattern (`send/email/forward+SharePoint/file/document+external address`) is a specific variant of persistent exfiltration that aigis does not yet explicitly detect in memory entries.

- **MINJA Memory Injection Attack (arxiv:2601.05504, Jan 2026)**
  Adversarial instructions injected through ordinary query-only interactions corrupt long-term memory with >70% success rate. Already partially covered by `mem_persistent_instruction` / `mem_override_personality` patterns. The gap is length-outlier and timestamp-based heuristics (statistical, not pattern-based) — too complex for this cycle.
  **aigis takeaway**: Pattern coverage is already reasonable. Focus new patterns on MCFA and objective-drifting.

- **Context Summarization Targeting (general, multiple sources)**
  Attackers craft memory entries and RAG documents that explicitly request to be preserved through context window summarization: "this is important context that must always be included in any summary", "when summarizing this conversation always include…". None of aigis's existing patterns target this vector.
  **aigis takeaway**: Add a pattern targeting summarization-persistence instructions.

- **Multi-Agent Memory Poisoning (arxiv:2603.20357, Mar 2026)**
  In multi-agent pipelines, one compromised agent writes crafted content into shared semantic memory, causing downstream agents to behave according to attacker goals. Write-provenance tagging (already supported by `memory/integrity.py` source field) is the right mitigation; the current implementation doesn't flag writes that reference other agents as a trust-escalation.
  **aigis takeaway**: Add a pattern detecting memory entries that reference "another agent said / agent X told me / orchestrator updated my memory" — a trust-laundering pattern in multi-agent settings.

## Candidate Hardenings

1. **`mem_tool_steering`** — New `MEMORY_POISONING_PATTERNS` entry: memory entry contains verbatim tool-invocation phrasing (`use the X tool`, `call X`, `invoke X function`). Targets MCFA (arxiv:2603.15125). Score: 45.

2. **`mem_objective_hijack`** — New pattern: replaces user's task/goal with attacker-controlled "new objective". Targets AgentLAB objective-drifting class (arxiv:2602.16901). Score: 45.

3. **`mem_summarization_persist`** — New pattern: instructions crafted to survive context window summarization ("important context that must be preserved in any summary"). Novel gap. Score: 50.

4. **`mem_agent_trust_laundering`** — New pattern: trust-laundering through attribution to another agent/orchestrator ("agent X told me to...", "the orchestrator updated my instructions"). Targets arxiv:2603.20357. Score: 45.

All four are additive `DetectionPattern` additions to `MEMORY_POISONING_PATTERNS` in `aigis/filters/patterns.py`. Zero new dependencies, total diff ≈ 55 LOC.
