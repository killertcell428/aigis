"""Tests for incident-postmortem-derived detection patterns (cycle 9, pass 3).

Covers:
- afe_n8n_expression_injection  (n8n CVE-2026-21858 CVSS 10.0 / CVE-2026-27493, CISA KEV)
- sc_langchain_dangerous_code   (LangChain allow_dangerous_code=True unsafe default, May 2026)
"""

from aigis.filters.patterns import SANDBOX_ESCAPE_PATTERNS, SUPPLY_CHAIN_PATTERNS


def _get_sandbox(rule_id: str):
    for p in SANDBOX_ESCAPE_PATTERNS:
        if p.id == rule_id:
            return p
    raise KeyError(f"Pattern {rule_id!r} not found in SANDBOX_ESCAPE_PATTERNS")


def _get_supply(rule_id: str):
    for p in SUPPLY_CHAIN_PATTERNS:
        if p.id == rule_id:
            return p
    raise KeyError(f"Pattern {rule_id!r} not found in SUPPLY_CHAIN_PATTERNS")


# ---------------------------------------------------------------------------
# afe_n8n_expression_injection — CVE-2026-21858 / CVE-2026-27493
# ---------------------------------------------------------------------------


class TestN8nExpressionInjection:
    def setup_method(self):
        self.pat = _get_sandbox("afe_n8n_expression_injection")

    # True positives — dangerous JavaScript in {{ }} expressions
    def test_child_process_execsync_detected(self):
        text = '{{ require("child_process").execSync("id").toString() }}'
        assert self.pat.pattern.search(text)

    def test_child_process_single_quote_detected(self):
        text = "{{ require('child_process').execSync('whoami') }}"
        assert self.pat.pattern.search(text)

    def test_process_env_secret_detected(self):
        text = "{{ process.env.SECRET }}"
        assert self.pat.pattern.search(text)

    def test_process_env_api_key_detected(self):
        text = "{{ process.env.OPENAI_API_KEY }}"
        assert self.pat.pattern.search(text)

    def test_process_main_module_detected(self):
        text = "{{ process.mainModule.require('child_process') }}"
        assert self.pat.pattern.search(text)

    def test_process_binding_detected(self):
        text = "{{ process.binding('fs') }}"
        assert self.pat.pattern.search(text)

    def test_execsync_standalone_detected(self):
        text = "{{ execSync('cat /etc/passwd') }}"
        assert self.pat.pattern.search(text)

    def test_spawnsync_detected(self):
        text = "{{ spawnSync('bash', ['-c', 'id']) }}"
        assert self.pat.pattern.search(text)

    def test_new_function_detected(self):
        text = "{{ new Function(\"return require('child_process')\") }}"
        assert self.pat.pattern.search(text)

    def test_n8n_field_with_injected_expression_detected(self):
        # Realistic n8n workflow JSON snippet with injected payload
        text = '"value": "{{ $json.name }}{{ require(\\"child_process\\").execSync(\\"id\\") }}"'
        assert self.pat.pattern.search(text)

    def test_base_score_is_significant(self):
        assert self.pat.base_score >= 70

    # True negatives — legitimate n8n expressions
    def test_json_field_access_benign(self):
        assert not self.pat.pattern.search("{{ $json.firstName }}")

    def test_node_item_access_benign(self):
        assert not self.pat.pattern.search('{{ $("HTTP Request").item.json.id }}')

    def test_now_format_benign(self):
        assert not self.pat.pattern.search("{{ $now.format('YYYY-MM-DD') }}")

    def test_workflow_id_benign(self):
        assert not self.pat.pattern.search("{{ $workflow.id }}")

    def test_env_without_braces_benign(self):
        # process.env reference outside {{ }} is not n8n expression injection
        assert not self.pat.pattern.search("Use process.env.SECRET in your Node.js app.")

    def test_normal_text_benign(self):
        assert not self.pat.pattern.search("Please summarize the document.")


# ---------------------------------------------------------------------------
# sc_langchain_dangerous_code — LangChain allow_dangerous_code=True
# ---------------------------------------------------------------------------


class TestLangchainDangerousCode:
    def setup_method(self):
        self.pat = _get_supply("sc_langchain_dangerous_code")

    # True positives — allow_dangerous_code=True in various forms
    def test_python_keyword_arg_detected(self):
        text = "agent = create_csv_agent(llm, 'data.csv', allow_dangerous_code=True)"
        assert self.pat.pattern.search(text)

    def test_python_with_spaces_detected(self):
        text = "allow_dangerous_code = True"
        assert self.pat.pattern.search(text)

    def test_json_config_lowercase_detected(self):
        text = '{"model": "gpt-4", "allow_dangerous_code": true}'
        assert self.pat.pattern.search(text)

    def test_python_dict_single_quote_detected(self):
        text = "config = {'allow_dangerous_code': True, 'verbose': True}"
        assert self.pat.pattern.search(text)

    def test_langflow_node_config_detected(self):
        text = "PandasDataFrameAgent(llm, df, allow_dangerous_code=True, verbose=False)"
        assert self.pat.pattern.search(text)

    def test_base_score_is_nonzero(self):
        assert self.pat.base_score >= 50

    # True negatives — safe references
    def test_false_value_benign(self):
        assert not self.pat.pattern.search("allow_dangerous_code=False")

    def test_json_false_benign(self):
        assert not self.pat.pattern.search('"allow_dangerous_code": false')

    def test_discussion_without_value_benign(self):
        assert not self.pat.pattern.search(
            "Never set allow_dangerous_code in production environments."
        )

    def test_unrelated_config_benign(self):
        assert not self.pat.pattern.search("verbose=True, return_intermediate_steps=True")

    def test_normal_text_benign(self):
        assert not self.pat.pattern.search("This agent analyzes CSV data securely.")
