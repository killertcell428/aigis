"""Goal-conditioned finite state machine for agent behaviour.

Inspired by MI9 (arxiv:2508.03858, Aug 2025), which adds FSM-based
conformance monitoring to runtime agent governance. Where ``monitor/drift.py``
already flags statistical drift from a learned baseline, an FSM lets
operators specify *exactly which transitions are allowed for a given goal*
— so "drift" becomes a hard policy violation rather than a soft anomaly.

Mechanism
---------
- Operator defines an ``AgentStateMachine`` with:
  * named states (e.g. ``planning``, ``gathering``, ``writing``, ``review``),
  * legal transitions between them,
  * per-state whitelists of tool names the agent is allowed to call.
- At runtime the ``FSMMonitor`` tracks the current state, and ``observe()``
  returns a ``FSMViolation`` whenever a transition or tool call is not in
  the spec. A violation is a hard signal — callers should block or
  escalate via ``monitor/containment.py``.
- The FSM is attached to a *goal*; the same agent can load different FSMs
  for different goals, matching MI9's "goal-conditioned" framing.

Why we add this
---------------
aigis already has behaviour tracking (``monitor/tracker.py``), baseline
learning (``monitor/baseline.py``), anomaly detection (``monitor/anomaly.py``),
and drift scoring (``monitor/drift.py``). What was missing is a way to
declare the *intended* control flow so that "this agent is not supposed to
call ``shell:exec`` while in the ``gathering`` state, ever" becomes
directly expressible and enforceable. Statistical drift cannot catch a
single-step escalation inside the normal-looking envelope.

Outcome
-------
- Operator-authored FSMs let teams encode their own agent-skeleton rules.
- Integrates with existing ``monitor/containment.py`` for graduated
  response (``warn → throttle → restrict → isolate → stop``).
- Zero dependency; pure stdlib, fits inside the ``spec_lang`` DSL family.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StateRule:
    """Per-state rule: which transitions and tools are allowed."""

    name: str
    allowed_tools: frozenset[str] = field(default_factory=frozenset)
    allowed_transitions: frozenset[str] = field(default_factory=frozenset)

    def can_call(self, tool: str) -> bool:
        return tool in self.allowed_tools

    def can_transition_to(self, state: str) -> bool:
        return state in self.allowed_transitions


@dataclass
class AgentStateMachine:
    """A goal-conditioned FSM spec."""

    goal: str
    initial_state: str
    states: dict[str, StateRule]
    terminal_states: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.initial_state not in self.states:
            raise ValueError(f"initial_state {self.initial_state!r} not in states")
        for name, rule in self.states.items():
            if rule.name != name:
                raise ValueError(f"state name mismatch: key={name!r} rule.name={rule.name!r}")
            for target in rule.allowed_transitions:
                if target not in self.states:
                    raise ValueError(f"transition to unknown state {target!r} from {name!r}")


@dataclass
class FSMViolation:
    """A single policy violation emitted by FSMMonitor."""

    kind: str  # "unknown_state" | "illegal_transition" | "forbidden_tool" | "terminal_continuation"
    goal: str
    from_state: str
    to_state: str | None
    tool: str | None
    message: str


class FSMMonitor:
    """Runtime conformance checker.

    Not thread-safe by design — callers that need concurrency should create
    one instance per agent session.
    """

    def __init__(self, fsm: AgentStateMachine) -> None:
        self.fsm = fsm
        self.current_state: str = fsm.initial_state
        self.history: list[tuple[str, str]] = []  # (state, tool or "->state")

    # ------------------------------------------------------------------
    # Observers
    # ------------------------------------------------------------------
    def observe_transition(self, new_state: str) -> FSMViolation | None:
        if self.current_state in self.fsm.terminal_states:
            return FSMViolation(
                kind="terminal_continuation",
                goal=self.fsm.goal,
                from_state=self.current_state,
                to_state=new_state,
                tool=None,
                message=f"transition from terminal state {self.current_state!r} is forbidden",
            )
        rule = self.fsm.states.get(self.current_state)
        if rule is None:
            return FSMViolation(
                kind="unknown_state",
                goal=self.fsm.goal,
                from_state=self.current_state,
                to_state=new_state,
                tool=None,
                message=f"current state {self.current_state!r} has no rule",
            )
        if new_state not in self.fsm.states:
            return FSMViolation(
                kind="unknown_state",
                goal=self.fsm.goal,
                from_state=self.current_state,
                to_state=new_state,
                tool=None,
                message=f"target state {new_state!r} is not in the FSM",
            )
        if not rule.can_transition_to(new_state):
            return FSMViolation(
                kind="illegal_transition",
                goal=self.fsm.goal,
                from_state=self.current_state,
                to_state=new_state,
                tool=None,
                message=f"transition {self.current_state!r} -> {new_state!r} not allowed by goal {self.fsm.goal!r}",
            )
        self.history.append((self.current_state, f"->{new_state}"))
        self.current_state = new_state
        return None

    def observe_tool_call(self, tool: str) -> FSMViolation | None:
        rule = self.fsm.states.get(self.current_state)
        if rule is None:
            return FSMViolation(
                kind="unknown_state",
                goal=self.fsm.goal,
                from_state=self.current_state,
                to_state=None,
                tool=tool,
                message=f"current state {self.current_state!r} has no rule",
            )
        if not rule.can_call(tool):
            return FSMViolation(
                kind="forbidden_tool",
                goal=self.fsm.goal,
                from_state=self.current_state,
                to_state=None,
                tool=tool,
                message=f"tool {tool!r} is not allowed in state {self.current_state!r} (goal={self.fsm.goal!r})",
            )
        self.history.append((self.current_state, tool))
        return None

    def reset(self) -> None:
        self.current_state = self.fsm.initial_state
        self.history.clear()
