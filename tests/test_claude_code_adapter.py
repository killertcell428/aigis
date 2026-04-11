"""Tests for aigis.adapters.claude_code module."""

import json

from aigis.adapters.claude_code import (
    HOOK_SCRIPT,
    TOOL_ACTION_MAP,
    generate_hooks_config,
    install_hooks,
)


class TestToolActionMap:
    def test_bash_maps_to_shell_exec(self):
        assert TOOL_ACTION_MAP["Bash"] == "shell:exec"

    def test_read_maps_to_file_read(self):
        assert TOOL_ACTION_MAP["Read"] == "file:read"

    def test_write_maps_to_file_write(self):
        assert TOOL_ACTION_MAP["Write"] == "file:write"

    def test_edit_maps_to_file_write(self):
        assert TOOL_ACTION_MAP["Edit"] == "file:write"

    def test_agent_maps_to_agent_spawn(self):
        assert TOOL_ACTION_MAP["Agent"] == "agent:spawn"

    def test_all_expected_tools_present(self):
        expected = {
            "Bash",
            "Read",
            "Write",
            "Edit",
            "Glob",
            "Grep",
            "WebFetch",
            "WebSearch",
            "Agent",
            "NotebookEdit",
        }
        assert set(TOOL_ACTION_MAP.keys()) == expected


class TestHookScript:
    def test_is_string(self):
        assert isinstance(HOOK_SCRIPT, str)

    def test_has_shebang(self):
        assert HOOK_SCRIPT.strip().startswith("#!/usr/bin/env python3")

    def test_contains_main_function(self):
        assert "def main():" in HOOK_SCRIPT

    def test_contains_map_action(self):
        assert "def _map_action(" in HOOK_SCRIPT

    def test_contains_extract_target(self):
        assert "def _extract_target(" in HOOK_SCRIPT

    def test_contains_get_scannable_text(self):
        assert "def _get_scannable_text(" in HOOK_SCRIPT

    def test_exit_code_2_for_deny(self):
        assert "sys.exit(2)" in HOOK_SCRIPT

    def test_reads_stdin(self):
        assert "sys.stdin.read()" in HOOK_SCRIPT


class TestGenerateHooksConfig:
    def test_returns_dict(self):
        config = generate_hooks_config()
        assert isinstance(config, dict)

    def test_has_hooks_key(self):
        config = generate_hooks_config()
        assert "hooks" in config

    def test_has_pre_tool_use(self):
        config = generate_hooks_config()
        assert "PreToolUse" in config["hooks"]

    def test_matcher_is_wildcard(self):
        config = generate_hooks_config()
        matchers = config["hooks"]["PreToolUse"]
        assert len(matchers) == 1
        assert matchers[0]["matcher"] == ".*"

    def test_hook_command_references_script(self):
        config = generate_hooks_config()
        hooks = config["hooks"]["PreToolUse"][0]["hooks"]
        assert len(hooks) == 1
        assert "aig-guard.py" in hooks[0]["command"]

    def test_hook_has_timeout(self):
        config = generate_hooks_config()
        hooks = config["hooks"]["PreToolUse"][0]["hooks"]
        assert hooks[0]["timeout"] == 10


class TestInstallHooks:
    def test_creates_hook_script(self, tmp_path):
        install_hooks(str(tmp_path))
        script = tmp_path / ".claude" / "hooks" / "aig-guard.py"
        assert script.exists()
        content = script.read_text(encoding="utf-8")
        assert "def main():" in content

    def test_creates_settings_json(self, tmp_path):
        install_hooks(str(tmp_path))
        settings = tmp_path / ".claude" / "settings.json"
        assert settings.exists()
        data = json.loads(settings.read_text(encoding="utf-8"))
        assert "hooks" in data
        assert "PreToolUse" in data["hooks"]

    def test_merges_with_existing_settings(self, tmp_path):
        # Create existing settings
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        settings_path = claude_dir / "settings.json"
        settings_path.write_text(json.dumps({"existingKey": "value"}), encoding="utf-8")

        install_hooks(str(tmp_path))

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["existingKey"] == "value"
        assert "hooks" in data

    def test_does_not_duplicate_hooks(self, tmp_path):
        # Install twice
        install_hooks(str(tmp_path))
        install_hooks(str(tmp_path))

        settings = tmp_path / ".claude" / "settings.json"
        data = json.loads(settings.read_text(encoding="utf-8"))
        # Should only have one PreToolUse matcher
        assert len(data["hooks"]["PreToolUse"]) == 1

    def test_handles_corrupt_settings_json(self, tmp_path):
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        settings_path = claude_dir / "settings.json"
        settings_path.write_text("not valid json", encoding="utf-8")

        # Should not raise
        install_hooks(str(tmp_path))

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert "hooks" in data
