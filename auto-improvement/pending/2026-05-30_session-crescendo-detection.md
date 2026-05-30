# Pending: Session-Level Crescendo Attack Detection

## Title
Session-level monitoring for Crescendo multi-turn jailbreak escalation

## Motivation
The Crescendo attack (Russinovich et al., USENIX Security 2025, arxiv:2404.01833) begins with
entirely benign prompts and gradually steers the model toward harmful content across multiple turns.
It exploits the model's tendency to follow recent context and its own prior outputs. The automated
variant (Crescendomation) outperformed all other single-technique jailbreaks on GPT-4 (+29–61%)
and Gemini-Pro (+49–71%) in the AdvBench benchmark.

Individual Crescendo turns contain no reliable lexical jailbreak signal — they are designed to
look like natural follow-up questions. Detection requires tracking conversation arc over multiple
turns: initial topic (benign), gradual topic drift, presence of sensitive keywords only appearing
in later turns.

## Proposed change
A `CrescendoMonitor` class in `aigis/monitor/` (or extending the existing behavioral monitor)
that:
1. Maintains a sliding window of the last N conversation turns
2. Computes the "topic cosine distance" or "keyword escalation score" between turn 1 and turn N
3. Flags when benign early turns are followed by turns containing high-risk keywords in the
   presence of a reference back to earlier content ("as we discussed", "building on", "going
   further", "now the next step")

## Why it was held back
- Requires session state — aigis currently operates as a stateless per-turn scanner
- Adds significant complexity (sliding window, session ID tracking, topic modeling)
- Likely requires at minimum 50+ LOC in non-test code, exceeding the single-cycle size limit
- Topic modeling without external dependencies requires heuristics that need calibration

## Which constraint blocked it
- Stateless architecture: aigis scans one message at a time; session state is not maintained
- LOC limit: a well-tested session monitor is > 100 LOC of non-test code

## Suggested next step for human reviewer
1. Review the session management infrastructure in `aigis/cross_session/` — it may already
   provide the scaffolding for per-session state.
2. If session state exists, a lightweight "topic escalation" heuristic (sensitive keyword count
   per turn, increasing monotonically) could be implemented in < 50 LOC.
3. Alternatively, document this as a Phase 3 SIEM integration item — SIEM systems naturally
   aggregate multi-turn session data and can apply the escalation heuristic at the log layer.
