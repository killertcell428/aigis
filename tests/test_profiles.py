"""Tests for composing role profiles from capabilities.

Two properties matter most here and have dedicated tests: an unnamed axis must
fall back to the most restrictive value (silence must not grant capability), and
the capability layer must never emit `review` (a prompt mid-task is exactly what
this design is trying to avoid).
"""

from __future__ import annotations

import json

import pytest

from aigis.activity import ActivityEvent
from aigis.policy import evaluate
from aigis.profiles import (
    CAPABILITY_VALUES,
    Profile,
    ProfileError,
    build_policy,
    describe,
    load_profile,
    validate,
)


def _profile(**capabilities: str) -> Profile:
    return Profile(name="Test", description="", capabilities=capabilities)


def _decide(profile: Profile, action: str, target: str = "*") -> str:
    policy = build_policy(profile)
    event = ActivityEvent(action=action, target=target)
    decision, _ = evaluate(event, policy)
    return decision


# --- defaults ------------------------------------------------------------------


def test_unnamed_axis_falls_back_to_most_restrictive():
    """Silence must not grant capability."""
    profile = _profile(web="read")

    assert profile.capability("shell") == "none"
    assert profile.capability("files") == "none"
    assert profile.capability("mcp") == "none"


def test_every_axis_default_is_the_first_listed_value():
    for axis, values in CAPABILITY_VALUES.items():
        assert _profile().capability(axis) == values[0]


# --- validation ----------------------------------------------------------------


def test_unknown_axis_is_rejected():
    """A typo like `shel:` would otherwise silently block everything."""
    with pytest.raises(ProfileError, match="unknown capability axis"):
        validate(_profile(shel="unrestricted"))


def test_invalid_value_is_rejected():
    with pytest.raises(ProfileError, match="invalid value"):
        validate(_profile(shell="allowlist"))


def test_error_names_the_allowed_values():
    with pytest.raises(ProfileError) as exc:
        validate(_profile(git="maybe"))
    assert "none" in str(exc.value) and "push" in str(exc.value)


# --- the no-review rule ---------------------------------------------------------


def test_capability_layer_never_emits_review():
    """A prompt mid-task is what this design avoids; judgement happens up front."""
    from aigis.profiles import _AXIS_BUILDERS

    for axis, builder in _AXIS_BUILDERS.items():
        for value in CAPABILITY_VALUES[axis]:
            for rule in builder(value):
                assert rule.decision in ("deny", "allow"), (
                    f"{axis}={value} produced {rule.decision!r} in {rule.id}"
                )


def test_only_git_emits_allow_rules():
    """Allows are evaluated before the baseline, so they can reach past a deny.

    Keeping the surface to one axis is what makes that safe to reason about. If a
    new axis needs an allow, it also needs denies for the dangerous shapes placed
    ahead of it — this test is the reminder.
    """
    from aigis.profiles import _AXIS_BUILDERS

    for axis, builder in _AXIS_BUILDERS.items():
        for value in CAPABILITY_VALUES[axis]:
            for rule in builder(value):
                if rule.decision == "allow":
                    assert axis == "git", f"{axis}={value} emitted an allow ({rule.id})"


# --- per-axis behaviour ---------------------------------------------------------


def test_shell_none_blocks_commands():
    assert _decide(_profile(shell="none"), "shell:exec", "ls") == "deny"


def test_shell_unrestricted_allows_ordinary_commands():
    assert _decide(_profile(shell="unrestricted"), "shell:exec", "ls") == "allow"


def test_web_none_blocks_fetch_and_search():
    profile = _profile(web="none")
    assert _decide(profile, "network:fetch", "https://example.com") == "deny"
    assert _decide(profile, "network:search", "query") == "deny"


def test_web_read_allows_fetch():
    assert _decide(_profile(web="read"), "network:fetch", "https://example.com") == "allow"


def test_files_read_blocks_writes_but_not_reads():
    profile = _profile(files="read")
    assert _decide(profile, "file:read", "notes.md") == "allow"
    assert _decide(profile, "file:write", "notes.md") == "deny"


def test_files_workspace_allows_both():
    profile = _profile(files="workspace")
    assert _decide(profile, "file:read", "notes.md") == "allow"
    assert _decide(profile, "file:write", "notes.md") == "allow"


def test_git_local_blocks_push_only():
    profile = _profile(shell="unrestricted", git="local")
    assert _decide(profile, "shell:exec", "git commit -m x") == "allow"
    assert _decide(profile, "shell:exec", "git push origin main") == "deny"


def test_git_push_blocks_force_push():
    profile = _profile(shell="unrestricted", git="push")
    assert _decide(profile, "shell:exec", "git push origin main") == "allow"
    assert _decide(profile, "shell:exec", "git push --force origin main") == "deny"
    assert _decide(profile, "shell:exec", "git push -f origin main") == "deny"


def test_git_none_blocks_all_git():
    profile = _profile(shell="unrestricted", git="none")
    assert _decide(profile, "shell:exec", "git status") == "deny"


def test_packages_none_blocks_installs_across_managers():
    profile = _profile(shell="unrestricted", packages="none")
    for command in ("npm install left-pad", "pip install requests", "uv add httpx"):
        assert _decide(profile, "shell:exec", command) == "deny", command


def test_packages_unrestricted_allows_installs():
    profile = _profile(shell="unrestricted", packages="unrestricted")
    assert _decide(profile, "shell:exec", "npm install left-pad") == "allow"


def test_mcp_none_blocks_tool_calls():
    assert _decide(_profile(mcp="none"), "mcp:tool_call", "some_tool") == "deny"


def test_mcp_approved_and_unrestricted_produce_the_same_policy():
    """The difference is managed-mcp.json, one layer up — not the Aigis policy."""
    approved = build_policy(_profile(mcp="approved"))
    unrestricted = build_policy(_profile(mcp="unrestricted"))

    assert [r.id for r in approved.rules] == [r.id for r in unrestricted.rules]


# --- baseline -------------------------------------------------------------------


def test_baseline_survives_the_most_permissive_profile():
    """No combination of capabilities may weaken the floor."""
    profile = _profile(
        web="read",
        files="unrestricted",
        shell="unrestricted",
        git="push",
        packages="unrestricted",
        mcp="unrestricted",
    )
    assert _decide(profile, "shell:exec", "rm -rf /") == "deny"
    assert _decide(profile, "file:write", ".env") == "deny"
    assert _decide(profile, "file:read", "~/.ssh/id_rsa") == "deny"
    # The one allow this design emits must not open a path past the floor.
    assert _decide(profile, "shell:exec", "git push --force origin main") == "deny"


def test_capability_rules_precede_baseline_rules():
    policy = build_policy(_profile(shell="none"))
    ids = [r.id for r in policy.rules]

    assert ids[0].startswith("cap_")
    assert "dangerous_commands" in ids


# --- loading --------------------------------------------------------------------


def test_load_profile_from_json(tmp_path):
    path = tmp_path / "marketing.json"
    path.write_text(
        json.dumps(
            {
                "name": "Marketing",
                "description": "Research and copy",
                "capabilities": {"web": "read", "files": "workspace"},
                "allow": {"mcp_servers": ["github"]},
            }
        ),
        encoding="utf-8",
    )

    profile = load_profile(path)

    assert profile.name == "Marketing"
    assert profile.capability("web") == "read"
    assert profile.capability("shell") == "none"  # unnamed → most restrictive
    assert profile.allow["mcp_servers"] == ["github"]


def test_load_profile_rejects_invalid_value(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"capabilities": {"shell": "sometimes"}}), encoding="utf-8")

    with pytest.raises(ProfileError):
        load_profile(path)


def test_load_profile_falls_back_to_filename_for_name(tmp_path):
    path = tmp_path / "design.json"
    path.write_text(json.dumps({"capabilities": {}}), encoding="utf-8")

    assert load_profile(path).name == "design"


# --- description ----------------------------------------------------------------


def test_describe_covers_every_axis():
    lines = describe(_profile(web="read", shell="none"))

    assert len(lines) == len(CAPABILITY_VALUES)
    assert any("Cannot run shell commands" in line for line in lines)
    assert any("Can fetch web pages" in line for line in lines)


def test_describe_has_a_line_for_every_axis_value_combination():
    """Every value needs prose, or the summary silently omits an axis."""
    for axis, values in CAPABILITY_VALUES.items():
        for value in values:
            lines = describe(_profile(**{axis: value}))
            assert any(line.startswith(axis) for line in lines)
