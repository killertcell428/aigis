# Pending: SLIP Cross-Session Lexical Insertion Detection

**Title:** Cross-session correlator heuristic for SLIP-style incremental keyword insertion

**Motivation:**
SLIP (Self-Jailbreaking via Lexical Insertion Prompting, arxiv:2601.02670, January 2026)
achieves 90–100% ASR (average 94.7%) across 11 tested models by casting jailbreaking as a
breadth-first tree search over multi-turn dialogues. Each individual turn inserts one or two
words from the attack goal into an otherwise benign prompt. The cumulative injection only
becomes visible across multiple turns — no single turn contains an obviously harmful prompt.

**Research finding that led to this idea:**
`auto-improvement/research/2026-05-23T03-06_3-jailbreak-extraction.md` — SLIP finding.

**Proposed change:**
Add a cross-session correlator heuristic in `aigis/cross_session/correlator.py` that:
1. Maintains a per-session sliding window of recent user turns.
2. Tracks keyword accumulation across turns: if the union of unique content words across the
   last N turns (N=5–10) matches a dangerous topic concept, raise a session-level alert.
3. Flag the session for human review, not block individual turns.

**Why it was held back:**
- Requires stateful session tracking with a time-windowed buffer — incompatible with the
  current single-turn filter architecture.
- The cross_session correlator module exists but is not yet wired to keyword accumulation.
- Total LOC impact would exceed 100 lines across non-test files.

**Constraint that blocked it:**
> "Any single change touching > 100 LOC across non-test files" — send to pending.

**Suggested next step for human reviewer:**
Review `aigis/cross_session/correlator.py` to see if a keyword-accumulation slot can be
added without requiring a full API redesign. If yes, implement as a separate PR targeting
the cross-session analysis layer rather than the input/output filter layer.
