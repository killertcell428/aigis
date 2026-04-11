"""Built-in default rule sets for the Policy DSL.

Provides sensible security defaults that can be used out of the box.
These rules encode common-sense restrictions aligned with the CaMeL
taint-tracking model: untrusted data should not be allowed to trigger
dangerous effects without explicit review.

Usage::

    from aigis.spec_lang.defaults import DEFAULT_RULES
    from aigis.spec_lang.parser import PolicyDSL

    dsl = PolicyDSL()
    for rule in DEFAULT_RULES:
        dsl.add_rule(rule)
"""

from __future__ import annotations

from aigis.spec_lang.parser import Enforcement, Predicate, Rule, Trigger

DEFAULT_RULES: list[Rule] = [
    # --- Untrusted data: block dangerous effects ---
    Rule(
        id="block_shell_untrusted",
        name="Block shell execution from untrusted data",
        trigger=Trigger(event="before_tool_call", tool_match="Bash|shell|execute"),
        predicates=[
            Predicate(type="resource_is", value="shell:exec"),
            Predicate(type="taint_is", value="untrusted"),
        ],
        enforcement=Enforcement(
            action="block",
            message="Shell execution blocked: data provenance is untrusted",
        ),
        priority=100,
    ),
    Rule(
        id="block_agent_spawn_untrusted",
        name="Block agent spawning from untrusted data",
        trigger=Trigger(event="before_tool_call", tool_match="*"),
        predicates=[
            Predicate(type="resource_is", value="agent:spawn"),
            Predicate(type="taint_is", value="untrusted"),
        ],
        enforcement=Enforcement(
            action="block",
            message="Agent spawning blocked: data provenance is untrusted",
        ),
        priority=100,
    ),
    Rule(
        id="block_mcp_tool_untrusted",
        name="Block MCP tool calls from untrusted data",
        trigger=Trigger(event="before_tool_call", tool_match="*"),
        predicates=[
            Predicate(type="resource_is", value="mcp:tool_call"),
            Predicate(type="taint_is", value="untrusted"),
        ],
        enforcement=Enforcement(
            action="block",
            message="MCP tool call blocked: data provenance is untrusted",
        ),
        priority=100,
    ),
    # --- Risk score thresholds ---
    Rule(
        id="block_high_risk",
        name="Block actions with risk score above 80",
        trigger=Trigger(event="before_tool_call", tool_match="*"),
        predicates=[
            Predicate(type="risk_above", value=80),
        ],
        enforcement=Enforcement(
            action="block",
            message="Action blocked: risk score exceeds safety threshold (80)",
        ),
        priority=90,
    ),
    Rule(
        id="warn_medium_risk",
        name="Warn on actions with risk score above 60",
        trigger=Trigger(event="before_tool_call", tool_match="*"),
        predicates=[
            Predicate(type="risk_above", value=60),
        ],
        enforcement=Enforcement(
            action="warn",
            message="Warning: elevated risk score detected (above 60)",
        ),
        priority=50,
    ),
    # --- Session abuse prevention ---
    Rule(
        id="throttle_excessive_actions",
        name="Throttle when action count exceeds 100 in session",
        trigger=Trigger(event="before_tool_call", tool_match="*"),
        predicates=[
            Predicate(type="action_count_above", value=100),
        ],
        enforcement=Enforcement(
            action="throttle",
            message="Session throttled: action count exceeds 100",
        ),
        priority=40,
    ),
    # --- Sensitive file protection ---
    Rule(
        id="block_env_file_write",
        name="Block file writes to .env files",
        trigger=Trigger(event="before_tool_call", tool_match="*"),
        predicates=[
            Predicate(type="resource_is", value="file:write"),
            Predicate(type="target_matches", value=".env*"),
        ],
        enforcement=Enforcement(
            action="block",
            message="File write blocked: .env files are protected",
        ),
        priority=95,
    ),
]
