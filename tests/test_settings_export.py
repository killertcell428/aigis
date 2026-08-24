"""Tests for exporting Claude Code permission settings from an Aigis policy.

The conversion is deliberately conservative: a rule that cannot be translated
exactly must be excluded and reported, never approximated. Most of these tests
exist to keep it that way, because a silently-loosened security rule is the one
failure mode that matters here.
"""

from __future__ import annotations

from aigis.policy import Policy, PolicyRule
from aigis.settings_export import (
    MANAGED_SETTINGS_PATHS,
    convert_rule,
    export_permissions,
)


def _policy(*rules: PolicyRule, default_decision: str = "allow") -> Policy:
    return Policy(
        name="Test Policy", version="1.0", rules=list(rules), default_decision=default_decision
    )


# --- decisions map to the right bucket ---------------------------------------


def test_decisions_map_to_buckets():
    policy = _policy(
        PolicyRule(id="d", action="shell:exec", target="rm -rf *", decision="deny"),
        PolicyRule(id="r", action="shell:exec", target="sudo *", decision="review"),
        PolicyRule(id="a", action="shell:exec", target="npm run *", decision="allow"),
    )
    result = export_permissions(policy)

    assert result.permissions["deny"] == ["Bash(rm -rf *)"]
    assert result.permissions["ask"] == ["Bash(sudo *)"]
    assert result.permissions["allow"] == ["Bash(npm run *)"]
    assert result.excluded == []


def test_review_becomes_ask_not_deny():
    """`review` means "prompt the human", which is Claude Code's `ask`."""
    policy = _policy(
        PolicyRule(id="r", action="shell:exec", target="git push *", decision="review")
    )
    result = export_permissions(policy)

    assert result.permissions["ask"] == ["Bash(git push *)"]
    assert result.permissions["deny"] == []


# --- action -> tool mapping ---------------------------------------------------


def test_file_write_maps_to_both_edit_and_write():
    """Claude Code separates editing an existing file from creating one."""
    policy = _policy(PolicyRule(id="env", action="file:write", target=".env*", decision="deny"))
    result = export_permissions(policy)

    assert result.permissions["deny"] == ["Edit(.env*)", "Write(.env*)"]


def test_file_wildcard_maps_to_every_file_tool():
    policy = _policy(PolicyRule(id="s", action="file:*", target="*secrets*", decision="review"))
    result = export_permissions(policy)

    assert result.permissions["ask"] == [
        "Read(*secrets*)",
        "Edit(*secrets*)",
        "Write(*secrets*)",
        "Glob(*secrets*)",
        "Grep(*secrets*)",
    ]


def test_network_actions_map_to_web_tools():
    policy = _policy(
        PolicyRule(id="f", action="network:fetch", target="*", decision="deny"),
        PolicyRule(id="s", action="network:search", target="*", decision="deny"),
    )
    result = export_permissions(policy)

    assert result.permissions["deny"] == ["WebFetch", "WebSearch"]


def test_mcp_tool_call_is_reported_not_approximated():
    """Which MCP servers exist is managed-mcp.json's business, not a permission rule."""
    policy = _policy(PolicyRule(id="m", action="mcp:tool_call", target="*", decision="deny"))
    result = export_permissions(policy)

    assert result.permissions["deny"] == []
    assert result.excluded[0].rule_id == "m"


def test_bare_star_target_becomes_bare_tool_rule():
    """`Bash(*)` is documented as equivalent to `Bash`; emit the short form."""
    policy = _policy(PolicyRule(id="all", action="shell:exec", target="*", decision="deny"))
    result = export_permissions(policy)

    assert result.permissions["deny"] == ["Bash"]


# --- exclusions: the important half ------------------------------------------


def test_leading_wildcard_is_excluded():
    """Bash specifiers anchor at the start of the command, fnmatch does not."""
    policy = _policy(PolicyRule(id="mkfs", action="shell:exec", target="*mkfs*", decision="deny"))
    result = export_permissions(policy)

    assert result.permissions["deny"] == []
    assert len(result.excluded) == 1
    assert result.excluded[0].rule_id == "mkfs"
    assert "starts with a wildcard" in result.excluded[0].reason


def test_shell_metacharacters_are_excluded():
    """Claude Code warns that content-matching rules are bypassable."""
    policy = _policy(PolicyRule(id="pipe", action="shell:exec", target="*| bash*", decision="deny"))
    result = export_permissions(policy)

    assert result.permissions["deny"] == []
    assert "metacharacters" in result.excluded[0].reason


def test_path_separator_is_excluded():
    """fnmatch `*` crosses directories; gitignore `*` does not."""
    policy = _policy(PolicyRule(id="ssh", action="file:*", target="*.ssh/*", decision="deny"))
    result = export_permissions(policy)

    assert result.permissions["deny"] == []
    assert "path separator" in result.excluded[0].reason
    assert result.excluded[0].suggestion is not None
    assert "**" in result.excluded[0].suggestion


def test_conditional_rule_is_excluded():
    """Exporting a conditional rule would drop the condition and over-apply it."""
    rule = PolicyRule(
        id="risky",
        action="*",
        target="*",
        decision="deny",
        conditions={"risk_above": 80},
    )
    result = export_permissions(_policy(rule))

    assert result.permissions["deny"] == []
    assert "conditional" in result.excluded[0].reason
    assert "risk_above" in result.excluded[0].reason


def test_unknown_action_is_excluded():
    policy = _policy(PolicyRule(id="spawn", action="agent:spawn", target="*", decision="review"))
    result = export_permissions(policy)

    assert result.permissions["ask"] == []
    assert "no Claude Code tool equivalent" in result.excluded[0].reason


def test_unknown_decision_is_excluded():
    policy = _policy(PolicyRule(id="weird", action="shell:exec", target="ls", decision="escalate"))
    result = export_permissions(policy)

    assert result.excluded[0].rule_id == "weird"
    assert "unknown decision" in result.excluded[0].reason


# --- suggestions must not be nonsense (regression) ---------------------------


def test_suggestion_does_not_name_a_flag_as_a_command():
    """`*--force*` must not come back as `Bash(--force:*)`."""
    rule = PolicyRule(id="force", action="shell:exec", target="*--force*", decision="deny")
    _, _, excluded = convert_rule(rule)

    assert excluded is not None
    assert "Bash(--force" not in (excluded.suggestion or "")


def test_suggestion_does_not_put_colon_star_mid_pattern():
    """`:*` is only recognised at the end of a pattern, so never suggest it mid-way."""
    rule = PolicyRule(id="dd", action="shell:exec", target="*dd if=*", decision="deny")
    _, _, excluded = convert_rule(rule)

    assert excluded is not None
    assert "Bash(dd if=:*)" not in (excluded.suggestion or "")


def test_suggestion_offers_anchored_form_for_a_plain_command():
    rule = PolicyRule(id="mkfs", action="shell:exec", target="*mkfs*", decision="deny")
    _, _, excluded = convert_rule(rule)

    assert excluded is not None
    assert "Bash(mkfs:*)" in (excluded.suggestion or "")


# --- settings body ------------------------------------------------------------


def test_managed_adds_disable_auto_mode():
    """The documented key is `disableAutoMode`, not `disableBypassPermissionsMode`."""
    policy = _policy(PolicyRule(id="d", action="shell:exec", target="rm -rf *", decision="deny"))

    settings = export_permissions(policy, managed=True).to_settings_dict()
    assert settings["disableAutoMode"] == "disable"

    unmanaged = export_permissions(policy, managed=False).to_settings_dict()
    assert "disableAutoMode" not in unmanaged


def test_empty_buckets_are_omitted_from_output():
    policy = _policy(PolicyRule(id="d", action="shell:exec", target="rm -rf *", decision="deny"))
    settings = export_permissions(policy).to_settings_dict()

    assert "deny" in settings["permissions"]
    assert "ask" not in settings["permissions"]
    assert "allow" not in settings["permissions"]


def test_deny_by_default_policy_sets_ask_mode():
    """Claude Code has no fail-closed defaultMode; `ask` is the closest posture."""
    policy = _policy(
        PolicyRule(id="d", action="shell:exec", target="rm -rf *", decision="deny"),
        default_decision="deny",
    )
    settings = export_permissions(policy).to_settings_dict()

    assert settings["permissions"]["defaultMode"] == "ask"


def test_allow_by_default_policy_omits_default_mode():
    policy = _policy(PolicyRule(id="d", action="shell:exec", target="rm -rf *", decision="deny"))
    settings = export_permissions(policy).to_settings_dict()

    assert "defaultMode" not in settings["permissions"]


def test_duplicate_specifiers_are_not_repeated():
    policy = _policy(
        PolicyRule(id="a", action="file:write", target=".env*", decision="deny"),
        PolicyRule(id="b", action="file:write", target=".env*", decision="deny"),
    )
    result = export_permissions(policy)

    assert result.permissions["deny"] == ["Edit(.env*)", "Write(.env*)"]


def test_managed_paths_cover_the_three_documented_locations():
    assert set(MANAGED_SETTINGS_PATHS) == {"macos", "linux", "windows"}
    assert MANAGED_SETTINGS_PATHS["linux"] == "/etc/claude-code/managed-settings.json"
