# Pending: Omission Constraint Decay Tracker

**Title:** Stateful Omission Constraint Decay Monitor

**Motivation:**
arxiv:2604.20911 (April 2026) demonstrates a fundamental asymmetry in long-context LLM behavior:
prohibition-type constraints ("do not reveal X", "never do Y") decay with conversation depth
while requirement-type constraints ("always format as JSON") remain stable. At turn 5, omission
compliance is 73%; by turn 16 it drops to 33%. The decay is driven by the constraint text being
progressively diluted by surrounding context (62–100% of the effect). Validated across 4,416
trials, 12 models, 8 providers. Critically, this is a passive attack — no adversarial injection
is required; context accumulation alone causes the safety degradation.

**Which research finding led to this idea:**
- arxiv:2604.20911 — "Omission Constraints Decay While Commission Constraints Persist in
  Long-Context LLM Agents"

**Proposed change:**
Add a stateful constraint-distance monitor that:
1. Identifies prohibition-type directives in the system prompt (phrases containing "never",
   "do not", "must not", "prohibited") at session start.
2. Tracks the approximate distance (in tokens or turns) since each prohibition was last
   echoed in the effective context window.
3. Emits a `CONSTRAINT_DECAY_RISK` warning event via the ActivityStream when the distance
   exceeds a configurable threshold (e.g., 50K tokens or 10 turns).
4. Optionally suggests re-issuing the system prompt's prohibitions as a reminder.

**Why it was held back:**
- Requires session-state tracking across multiple scan calls, which aigis currently does not
  maintain (each scan call is stateless with respect to other calls).
- Token counting without access to the model's tokenizer is approximate; a pure character-count
  heuristic may be inaccurate for different models.
- Would require a new `SessionMonitor` or `ConversationGuard` API surface that tracks system
  prompt content across turns — a meaningful architectural addition.

**Which constraint blocked it:**
- No suitable zero-dependency, stateless implementation within 100 LOC.
- Requires a new public API class (`SessionMonitor` or similar), which is an API surface change
  that exceeds the "small safe hardening" threshold.

**Suggested next step for human reviewer:**
1. Define a `ConversationGuard` class that wraps `Scanner` and maintains session state across
   turns, tracking which prohibitions were issued in the system prompt and when they were last
   seen in context.
2. Add a configurable `constraint_decay_threshold` (in turns or token estimate) parameter.
3. Emit a `CONSTRAINT_DECAY_WARNING` ActivityEvent rather than blocking — this is observational,
   not actionable in real time, and different operators have different turn depths.
4. Add tests with synthetic multi-turn conversation sessions where a prohibition drifts beyond
   the threshold.
