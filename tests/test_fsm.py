"""Tests for the goal-conditioned FSM monitor."""
import pytest

from aigis.spec_lang.fsm import (
    AgentStateMachine,
    FSMMonitor,
    StateRule,
)


def _sample_fsm() -> AgentStateMachine:
    return AgentStateMachine(
        goal="write_report",
        initial_state="planning",
        states={
            "planning": StateRule(
                name="planning",
                allowed_tools=frozenset({"search", "note"}),
                allowed_transitions=frozenset({"gathering"}),
            ),
            "gathering": StateRule(
                name="gathering",
                allowed_tools=frozenset({"search", "fetch_url"}),
                allowed_transitions=frozenset({"writing"}),
            ),
            "writing": StateRule(
                name="writing",
                allowed_tools=frozenset({"edit_doc"}),
                allowed_transitions=frozenset({"done"}),
            ),
            "done": StateRule(name="done"),
        },
        terminal_states=frozenset({"done"}),
    )


def test_allowed_tool_passes():
    m = FSMMonitor(_sample_fsm())
    assert m.observe_tool_call("search") is None


def test_forbidden_tool_flagged():
    m = FSMMonitor(_sample_fsm())
    v = m.observe_tool_call("shell:exec")
    assert v is not None
    assert v.kind == "forbidden_tool"
    assert v.tool == "shell:exec"


def test_illegal_transition_flagged():
    m = FSMMonitor(_sample_fsm())
    v = m.observe_transition("writing")  # skip gathering
    assert v is not None and v.kind == "illegal_transition"


def test_legal_transition_advances_state():
    m = FSMMonitor(_sample_fsm())
    assert m.observe_transition("gathering") is None
    assert m.current_state == "gathering"
    # fetch_url is allowed in gathering but not planning
    assert m.observe_tool_call("fetch_url") is None


def test_tool_allowed_in_one_state_forbidden_in_another():
    m = FSMMonitor(_sample_fsm())
    m.observe_transition("gathering")
    m.observe_transition("writing")
    v = m.observe_tool_call("fetch_url")
    assert v is not None and v.kind == "forbidden_tool"


def test_terminal_state_blocks_further_transitions():
    m = FSMMonitor(_sample_fsm())
    m.observe_transition("gathering")
    m.observe_transition("writing")
    m.observe_transition("done")
    v = m.observe_transition("planning")
    assert v is not None and v.kind == "terminal_continuation"


def test_bad_initial_state_rejected():
    with pytest.raises(ValueError):
        AgentStateMachine(
            goal="x",
            initial_state="nope",
            states={"planning": StateRule(name="planning")},
        )


def test_transition_to_unknown_state_rejected_at_spec_load():
    with pytest.raises(ValueError):
        AgentStateMachine(
            goal="x",
            initial_state="a",
            states={
                "a": StateRule(name="a", allowed_transitions=frozenset({"ghost"})),
            },
        )
