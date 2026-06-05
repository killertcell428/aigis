# Pending: Stateful Multi-Turn Objective Drift Detection

**Title:** Stateful conversation-level intent drift tracking in `AgentMessageScanner`

**Motivation:**
DeepContext (arxiv:2602.16935, Feb 2026) documents that "Crescendo"-style attacks
distribute harmful intent across multiple turns. Each individual turn looks benign; the
attack signal only emerges as the *gradient of risk over time*. The current
`AgentMessageScanner` is stateless — it evaluates each message in isolation and cannot
detect escalation patterns across a conversation.

**Research finding that led to this idea:**
DeepContext proposes GRU-based hidden state tracking across turns, achieving average
early detection at 4.24 turns before explicit harm. The paper also shows that stateless
per-message classifiers reliably miss Crescendo, ActorAttack, and FITD-style attacks
because benign preambles dilute the adversarial signal below detection thresholds.

**Proposed change:**
Add an optional `ConversationContext` accumulator to `AgentMessageScanner.scan_conversation()`
that maintains a running risk score across turns and flags a conversation when:
- cumulative risk score exceeds a configurable threshold across N turns, or
- risk score increases monotonically for K consecutive turns without a benign reset.

This would be an opt-in API extension: `scan_conversation(messages, stateful=True)`.

**Why it was held back:**
- Adding stateful conversation tracking to `AgentMessageScanner` is an architectural
  change that touches the public interface.
- A correct implementation would exceed 100 non-test LOC.
- Requires careful threshold calibration to avoid high false positive rates on legitimate
  multi-step agent workflows.

**Which constraint blocked it:**
- "Any single change touching > 100 LOC across non-test files" → send to pending.
- "Any breaking public API change" → requires careful backward-compat design.

**Suggested next step for human reviewer:**
Design the `ConversationContext` data class and calibrate thresholds against the AgentLAB
benchmark (arxiv:2602.16901) before implementation. Consider whether the threshold should
be configurable at `AgentMessageScanner.__init__()` time.
