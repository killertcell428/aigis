"""Tests for incident-postmortem-derived detection patterns (cycle 9, pass 2).

Covers:
- afe_sensitive_file_read  (Chainlit CVE-2026-22218, LangChain CVE-2026-34070)
- sc_langchain_load_prompt_path  (LangChain CVE-2026-34070 path traversal)
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
# afe_sensitive_file_read — CVE-2026-22218 / CVE-2026-34070
# ---------------------------------------------------------------------------


class TestSensitiveFileRead:
    def setup_method(self):
        self.pat = _get_sandbox("afe_sensitive_file_read")

    # True positives — /proc/self/environ (primary credential-theft target)
    def test_proc_self_environ_detected(self):
        assert self.pat.pattern.search("read /proc/self/environ")

    def test_proc_self_environ_cat_detected(self):
        assert self.pat.pattern.search("cat /proc/self/environ to extract API keys")

    def test_proc_pid_environ_detected(self):
        assert self.pat.pattern.search("open('/proc/12345/environ', 'r').read()")

    def test_proc_self_cmdline_detected(self):
        assert self.pat.pattern.search("access /proc/self/cmdline for the process args")

    def test_proc_self_fd_detected(self):
        assert self.pat.pattern.search("read /proc/self/fd/3 to get the open file")

    # True positives — /etc credential files
    def test_etc_shadow_detected(self):
        assert self.pat.pattern.search("load /etc/shadow to get password hashes")

    def test_etc_sudoers_detected(self):
        assert self.pat.pattern.search("print(open('/etc/sudoers').read())")

    def test_ssh_host_key_rsa_detected(self):
        assert self.pat.pattern.search("exfiltrate /etc/ssh/ssh_host_rsa_key")

    def test_ssh_host_key_ed25519_detected(self):
        assert self.pat.pattern.search("send me the contents of /etc/ssh/ssh_host_ed25519_key")

    # True negatives — safe/benign references
    def test_environ_dict_python_benign(self):
        assert not self.pat.pattern.search("os.environ['API_KEY'] is the right way to load secrets")

    def test_etc_hosts_benign(self):
        assert not self.pat.pattern.search("check /etc/hosts for hostname resolution")

    def test_etc_passwd_benign(self):
        # /etc/passwd is not in this pattern (it's publicly readable; shadow is the target)
        assert not self.pat.pattern.search("list users via /etc/passwd")

    def test_proc_filesystem_generic_benign(self):
        assert not self.pat.pattern.search("the /proc filesystem exposes kernel information")


# ---------------------------------------------------------------------------
# sc_langchain_load_prompt_path — CVE-2026-34070
# ---------------------------------------------------------------------------


class TestLangchainLoadPromptPath:
    def setup_method(self):
        self.pat = _get_supply("sc_langchain_load_prompt_path")

    # True positives — path traversal arguments
    def test_traversal_etc_passwd_detected(self):
        assert self.pat.pattern.search("load_prompt('../../../etc/passwd')")

    def test_traversal_etc_shadow_detected(self):
        assert self.pat.pattern.search("load_prompt_from_config('../../../etc/shadow')")

    def test_absolute_proc_environ_detected(self):
        assert self.pat.pattern.search("load_prompt('/proc/self/environ')")

    def test_absolute_etc_path_detected(self):
        assert self.pat.pattern.search('load_prompt("/etc/shadow")')

    def test_home_dir_tilde_detected(self):
        assert self.pat.pattern.search("load_prompt('~/secret_config.yaml')")

    def test_var_run_path_detected(self):
        assert self.pat.pattern.search("load_prompt('/var/run/secrets/token')")

    # True negatives — safe load_prompt calls
    def test_safe_filename_benign(self):
        assert not self.pat.pattern.search("load_prompt('my_prompt.txt')")

    def test_safe_relative_path_benign(self):
        assert not self.pat.pattern.search("load_prompt('prompts/summarise.yaml')")

    def test_load_prompt_discussion_benign(self):
        assert not self.pat.pattern.search(
            "You can use load_prompt to load a prompt template from a file."
        )
