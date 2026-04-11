"""LangGraph integration for Aigis.

Provides a ``GuardNode`` that can be inserted into any LangGraph ``StateGraph``
as a pre-LLM security scanning step.  The node blocks the graph execution and
raises ``GuardianBlockedError`` when the current user message exceeds the
configured risk threshold.

Usage (simplest form)::

    from langgraph.graph import StateGraph, END
    from aigis.middleware.langgraph import GuardNode, GuardState

    # Define your graph state — must include "messages" key
    builder = StateGraph(GuardState)

    # Add the guard node first, before your LLM node
    guard_node = GuardNode()
    builder.add_node("guard", guard_node)
    builder.add_node("llm", your_llm_node)

    builder.set_entry_point("guard")
    builder.add_edge("guard", "llm")
    builder.add_edge("llm", END)

    graph = builder.compile()

    # Invoke — GuardianBlockedError is raised if input is unsafe
    try:
        result = graph.invoke({"messages": [{"role": "user", "content": user_input}]})
    except GuardianBlockedError as e:
        print(f"Blocked: {e.reasons}")

Conditional routing (pass-through vs block)::

    from aigis.middleware.langgraph import GuardNode, GuardState, GUARD_BLOCKED

    guard_node = GuardNode(raise_on_block=False)  # don't raise, route instead

    builder.add_node("guard", guard_node)
    builder.add_conditional_edges(
        "guard",
        lambda state: GUARD_BLOCKED if state.get("guard_blocked") else "llm",
        {GUARD_BLOCKED: END, "llm": "llm"},
    )
"""

from __future__ import annotations

from typing import Any

GUARD_BLOCKED = "__guard_blocked__"


class GuardianBlockedError(Exception):
    """Raised by GuardNode when the input exceeds the risk threshold.

    Attributes:
        risk_score: Integer risk score (0-100).
        reasons: List of matched rule names.
        remediation: Remediation hints dict from the Guard result.
    """

    def __init__(
        self,
        message: str,
        risk_score: int = 0,
        reasons: list[str] | None = None,
        remediation: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.risk_score = risk_score
        self.reasons = reasons or []
        self.remediation = remediation or {}


# ---------------------------------------------------------------------------
# Type alias for state dicts used in LangGraph graphs.
# Users can subclass / extend this TypedDict as needed.
# ---------------------------------------------------------------------------
try:
    from typing import TypedDict

    class GuardState(TypedDict, total=False):
        """Minimal state schema that GuardNode expects.

        Your own state may extend this with additional keys.

        Attributes:
            messages: List of OpenAI-style ``{"role": ..., "content": ...}``
                      dicts.  GuardNode scans the *last* user message.
            guard_blocked: Set to ``True`` by GuardNode when input is blocked
                           and ``raise_on_block=False``.
            guard_risk_score: Integer risk score of the last scanned message.
            guard_reasons: List of rule names that fired.
        """

        messages: list[dict[str, Any]]
        guard_blocked: bool
        guard_risk_score: int
        guard_reasons: list[str]

except ImportError:
    GuardState = dict  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# GuardNode
# ---------------------------------------------------------------------------


class GuardNode:
    """LangGraph node that scans user messages before they reach the LLM.

    Args:
        policy: Built-in policy name (``"default"``, ``"strict"``,
                ``"permissive"``) or path to a YAML policy file.
        raise_on_block: When ``True`` (default) raise ``GuardianBlockedError``
                        on a blocked input.  When ``False`` set
                        ``state["guard_blocked"] = True`` and return the state
                        so the graph can route elsewhere via conditional edges.
        scan_all_messages: When ``True`` scan every user message in the
                           ``messages`` list.  When ``False`` (default) only
                           scan the last user message.
    """

    def __init__(
        self,
        policy: str = "default",
        raise_on_block: bool = True,
        scan_all_messages: bool = False,
    ) -> None:
        from aigis.guard import Guard

        self._guard = Guard(policy=policy)
        self._raise_on_block = raise_on_block
        self._scan_all = scan_all_messages

    def __call__(self, state: dict[str, Any]) -> dict[str, Any]:
        """Scan the incoming message(s) and update state.

        This method is compatible with both sync and async LangGraph invocations
        (LangGraph calls sync nodes in a thread pool automatically).

        Args:
            state: The current graph state dict.  Must contain a ``"messages"``
                   key with a list of OpenAI-style message dicts.

        Returns:
            Updated state dict with ``guard_blocked``, ``guard_risk_score``, and
            ``guard_reasons`` set.

        Raises:
            GuardianBlockedError: When the input is blocked and
                                  ``raise_on_block=True``.
        """
        messages: list[dict[str, Any]] = state.get("messages", [])

        if self._scan_all:
            # Scan all user messages
            texts = [
                m.get("content", "")
                for m in messages
                if m.get("role") == "user" and isinstance(m.get("content"), str)
            ]
        else:
            # Scan only the last user message
            user_messages = [m for m in messages if m.get("role") == "user" and m.get("content")]
            texts = [user_messages[-1]["content"]] if user_messages else []

        # Combine all texts into one scan (for multi-turn context)
        combined = "\n".join(texts)
        if not combined.strip():
            return {
                **state,
                "guard_blocked": False,
                "guard_risk_score": 0,
                "guard_reasons": [],
            }

        result = self._guard.check_input(combined)

        if result.blocked:
            if self._raise_on_block:
                raise GuardianBlockedError(
                    f"Aigis blocked this request "
                    f"(score={result.risk_score}, reasons={result.reasons})",
                    risk_score=result.risk_score,
                    reasons=result.reasons,
                    remediation=result.remediation,
                )
            return {
                **state,
                "guard_blocked": True,
                "guard_risk_score": result.risk_score,
                "guard_reasons": result.reasons,
            }

        return {
            **state,
            "guard_blocked": False,
            "guard_risk_score": result.risk_score,
            "guard_reasons": result.reasons,
        }
