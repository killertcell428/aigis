"""Built-in detection patterns for security threats.

Each pattern has:
  - id: unique identifier
  - name: human-readable name
  - category: threat category
  - pattern: compiled regex
  - base_score: risk points added when matched
  - description: explanation
  - owasp_ref: OWASP LLM Top 10 or CWE classification
  - remediation_hint: actionable guidance for developers/reviewers
"""
import re
from dataclasses import dataclass, field


@dataclass
class DetectionPattern:
    """A single detection rule with remediation metadata."""

    id: str
    name: str
    category: str
    pattern: re.Pattern
    base_score: int
    description: str
    owasp_ref: str = ""
    remediation_hint: str = ""
    enabled: bool = True


def _p(pattern: str, flags: int = re.IGNORECASE | re.DOTALL) -> re.Pattern:
    return re.compile(pattern, flags)


# ---------------------------------------------------------------------------
# Prompt Injection Patterns
# ---------------------------------------------------------------------------
PROMPT_INJECTION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="pi_ignore_instructions",
        name="Ignore Previous Instructions",
        category="prompt_injection",
        pattern=_p(
            r"(ignore|disregard|forget|override|bypass)\s+(previous|prior|all|the|above|your|any)"
            r"\s+(instructions?|rules?|guidelines?|prompts?|constraints?|directions?|system)"
        ),
        base_score=40,
        description="Classic 'ignore previous instructions' prompt injection attempt.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="If you intended to reference previous content, rephrase to avoid instruction-override patterns. Example: 'skip the earlier section' instead of 'ignore previous instructions'.",
    ),
    DetectionPattern(
        id="pi_jailbreak_dan",
        name="DAN / Jailbreak Persona",
        category="prompt_injection",
        pattern=_p(
            r"\b(DAN|jailbreak|do\s+anything\s+now|you\s+are\s+now\s+a|pretend\s+you\s+are"
            r"|act\s+as\s+if\s+you\s+have\s+no\s+restrictions|roleplay\s+as\s+an\s+ai\s+without)"
        ),
        base_score=50,
        description="DAN or jailbreak persona injection attempting to remove AI restrictions.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="Jailbreak attempts try to bypass AI safety guardrails. This pattern is almost always malicious. For legitimate role-play, define the role in the system prompt.",
    ),
    DetectionPattern(
        id="pi_system_prompt_leak",
        name="System Prompt Extraction",
        category="prompt_injection",
        pattern=_p(
            r"(print|show|reveal|output|repeat|tell\s+me|what\s+is|display)\s+"
            r"(your\s+)?(system\s+prompt|initial\s+prompt|original\s+instructions?|"
            r"base\s+prompt|full\s+prompt|hidden\s+instructions?)"
        ),
        base_score=45,
        description="Attempt to extract the system prompt from the AI.",
        owasp_ref="OWASP LLM07: System Prompt Leakage",
        remediation_hint="System prompt extraction can expose business logic and security rules. Use application logging to debug prompt behavior instead.",
    ),
    DetectionPattern(
        id="pi_new_instructions",
        name="Instruction Override",
        category="prompt_injection",
        pattern=_p(
            r"(from\s+now\s+on|henceforth|starting\s+now|new\s+instructions?:"
            r"|your\s+new\s+task\s+is|you\s+must\s+now|your\s+only\s+goal\s+is)"
        ),
        base_score=35,
        description="Attempts to override AI behavior with new instructions.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="This looks like an attempt to change the AI's base behavior. Rephrase: 'Additionally, please also...' instead of 'From now on...'.",
    ),
    DetectionPattern(
        id="pi_role_switch",
        name="Malicious Role Switch",
        category="prompt_injection",
        pattern=_p(
            r"(you\s+are\s+now|you\s+will\s+act\s+as|switch\s+to\s+mode|enter\s+"
            r"(dev|developer|god|admin|root|unrestricted|uncensored)\s+mode)"
        ),
        base_score=45,
        description="Attempts to switch AI to a malicious or unrestricted role.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="Role-switch attacks try to elevate AI privileges. Configure roles in the system prompt through application code, not user input.",
    ),
    DetectionPattern(
        id="pi_encoding_bypass",
        name="Encoding/Obfuscation Bypass",
        category="prompt_injection",
        pattern=_p(
            r"(base64|rot13|hex\s+encoded?|unicode\s+escape|url\s+encoded?)\s+"
            r"(instruction|command|prompt|message)"
        ),
        base_score=55,
        description="Attempts to use encoding to bypass filters.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="Encoded payloads are a filter-evasion technique. Decode data in application code before sending to the LLM.",
    ),
]

# ---------------------------------------------------------------------------
# SQL Injection Patterns
# ---------------------------------------------------------------------------
SQL_INJECTION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="sqli_union_select", name="UNION SELECT", category="sql_injection",
        pattern=_p(r"(union\s+(all\s+)?select)"), base_score=70,
        description="UNION-based SQL injection attempt.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="UNION SELECT extracts data from other tables. For text-to-SQL apps, use parameterized queries and allowlists.",
    ),
    DetectionPattern(
        id="sqli_drop_table", name="DROP TABLE", category="sql_injection",
        pattern=_p(r"\b(drop\s+table|drop\s+database|truncate\s+table)\b"), base_score=80,
        description="Destructive DDL SQL injection attempt.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="Destructive SQL can cause data loss. Restrict AI to SELECT-only queries and use read-only database connections.",
    ),
    DetectionPattern(
        id="sqli_boolean_blind", name="Boolean-based Blind SQLi", category="sql_injection",
        pattern=_p(r"(\'\s*(or|and)\s*[\'\d].*=.*[\'\d]|\b(or|and)\s+\d+\s*=\s*\d+)"), base_score=65,
        description="Boolean-based blind SQL injection.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="Boolean injection probes database responses. Use parameterized queries and validate generated SQL.",
    ),
    DetectionPattern(
        id="sqli_comment", name="SQL Comment Injection", category="sql_injection",
        pattern=_p(r"(--|#|\/\*|\*\/)\s*(or|and|select|insert|update|delete|drop)"), base_score=55,
        description="SQL comment-based injection to truncate queries.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="SQL comments can truncate queries. Wrap SQL syntax in markdown code blocks when discussing.",
    ),
    DetectionPattern(
        id="sqli_stacked", name="Stacked Queries", category="sql_injection",
        pattern=_p(r";\s*(select|insert|update|delete|drop|create|alter|exec)\b"), base_score=70,
        description="Stacked query SQL injection.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="Disable multi-statement execution in your database driver and use allowlists for permitted SQL operations.",
    ),
    DetectionPattern(
        id="sqli_sleep_benchmark", name="Time-based Blind SQLi", category="sql_injection",
        pattern=_p(r"\b(sleep\s*\(\d+\)|benchmark\s*\(\d+|waitfor\s+delay)\b"), base_score=75,
        description="Time-based blind SQL injection using sleep/benchmark.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="Set query timeouts and monitor for abnormally slow queries.",
    ),
]

# ---------------------------------------------------------------------------
# Data Exfiltration Patterns
# ---------------------------------------------------------------------------
DATA_EXFIL_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="exfil_pii_request", name="PII Extraction Request", category="data_exfiltration",
        pattern=_p(
            r"(list|extract|export|dump|retrieve)\s+(all\s+)?"
            r"(user(s|\s+data)?|customer(s|\s+data)?|employee(s|\s+records?)?|"
            r"personal\s+data|private\s+information|credentials?)"
        ),
        base_score=50,
        description="Attempts to extract personally identifiable information.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="Use aggregated/anonymized datasets instead. Never ask AI to retrieve raw PII from connected systems.",
    ),
    DetectionPattern(
        id="exfil_api_keys", name="API Key / Secret Extraction", category="data_exfiltration",
        pattern=_p(
            r"(show|give|tell|print|reveal)\s+(me\s+)?(the\s+)?"
            r"(api\s+key|secret\s+key|private\s+key|access\s+token|password|credentials?)"
        ),
        base_score=60,
        description="Attempts to extract API keys or secrets.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="Use your organization's secret manager (AWS Secrets Manager, Vault, etc.) to access keys securely.",
    ),
]

# ---------------------------------------------------------------------------
# Command Injection Patterns
# ---------------------------------------------------------------------------
COMMAND_INJECTION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="cmdi_shell", name="Shell Command Injection", category="command_injection",
        pattern=_p(
            r"(\b(exec|system|shell_exec|popen|subprocess|os\.system|eval)\s*\(|"
            r"\$\(.*\)|`[^`]+`|\|\s*(bash|sh|cmd|powershell)\b)"
        ),
        base_score=70,
        description="Shell command injection attempt.",
        owasp_ref="CWE-78: OS Command Injection",
        remediation_hint="Shell commands in AI prompts can lead to RCE. Use markdown code blocks for code discussion. Never connect AI to shell without sandboxing.",
    ),
    DetectionPattern(
        id="cmdi_path_traversal", name="Path Traversal", category="command_injection",
        pattern=_p(r"(\.\.\/|\.\.\\|%2e%2e%2f|%252e%252e%252f)"),
        base_score=60,
        description="Path traversal attempt.",
        owasp_ref="CWE-22: Path Traversal",
        remediation_hint="Use absolute paths or restrict file access to a designated directory.",
    ),
]

# ---------------------------------------------------------------------------
# PII Detection Patterns (Input — prevent sending PII to LLMs)
# ---------------------------------------------------------------------------
PII_INPUT_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="pii_jp_phone", name="Japanese Phone Number", category="pii_input",
        pattern=_p(r"(0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4}|0[789]0[-\s]?\d{4}[-\s]?\d{4})"),
        base_score=40,
        description="Japanese phone number (landline or mobile) detected in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="電話番号がLLMに送信されます。テストデータの場合は 090-0000-0000 のようなダミー番号に置き換えてください。",
    ),
    DetectionPattern(
        id="pii_jp_my_number", name="Japanese My Number (Individual)", category="pii_input",
        pattern=_p(r"\b\d{4}\s?\d{4}\s?\d{4}\b"), base_score=70,
        description="Japanese My Number (individual, 12 digits) pattern detected in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="マイナンバーは特定個人情報です。絶対にLLMに送信しないでください。",
    ),
    DetectionPattern(
        id="pii_jp_corporate_number", name="Japanese Corporate Number", category="pii_input",
        pattern=_p(r"\b[1-9]\d{12}\b"), base_score=35,
        description="Japanese Corporate Number (13 digits) detected in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="法人番号が検出されました。公開情報ですがコンテキストによっては機密扱いが必要です。",
    ),
    DetectionPattern(
        id="pii_jp_postal_code", name="Japanese Postal Code", category="pii_input",
        pattern=_p(r"〒?\s?\d{3}[-ー]\d{4}"), base_score=25,
        description="Japanese postal code detected in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="郵便番号単体のリスクは低いですが、住所と組み合わさると個人特定につながります。",
    ),
    DetectionPattern(
        id="pii_jp_address", name="Japanese Address", category="pii_input",
        pattern=_p(
            r"(東京都|北海道|(?:京都|大阪)府|.{2,3}県)"
            r".{1,6}[市区町村郡].{1,10}[0-9０-９\-ー]+"
        ),
        base_score=40,
        description="Japanese street address pattern detected in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="詳細な住所は個人特定情報です。市区町村レベルまでに留めてください。",
    ),
    DetectionPattern(
        id="pii_jp_bank_account", name="Japanese Bank Account", category="pii_input",
        pattern=_p(
            r"(銀行|信用金庫|信金|ゆうちょ).{0,10}(支店|本店).{0,10}"
            r"(普通|当座|貯蓄).{0,5}\d{6,8}"
        ),
        base_score=65,
        description="Japanese bank account details detected in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="口座情報は金融犯罪リスクがあります。具体的な口座番号を含めないでください。",
    ),
    DetectionPattern(
        id="pii_email_input", name="Email Address in Input", category="pii_input",
        pattern=_p(
            r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}[\s,;]){2,}"
        ),
        base_score=35,
        description="Multiple email addresses detected in input (possible PII exposure).",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="Multiple email addresses may indicate bulk PII exposure. Use anonymized identifiers instead.",
    ),
    DetectionPattern(
        id="pii_credit_card_input", name="Credit Card in Input", category="pii_input",
        pattern=_p(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b"),
        base_score=70,
        description="Credit card number detected in input — should not be sent to LLM.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure / PCI-DSS",
        remediation_hint="Credit card numbers must never be sent to LLMs (PCI-DSS violation). Use tokenized references or masked numbers.",
    ),
    DetectionPattern(
        id="pii_ssn_input", name="SSN in Input", category="pii_input",
        pattern=_p(r"\b\d{3}-\d{2}-\d{4}\b"), base_score=65,
        description="US Social Security Number detected in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="Never include real SSNs in AI prompts. Use IRS test range: 987-65-4320 to 987-65-4329.",
    ),
    DetectionPattern(
        id="pii_api_key_input", name="API Key / Secret in Input", category="pii_input",
        pattern=_p(
            r"(sk-[a-zA-Z0-9]{20,}|AIza[0-9A-Za-z\-_]{35}|"
            r"ghp_[0-9A-Za-z]{36}|xox[baprs]-[0-9a-zA-Z\-]+|"
            r"AKIA[0-9A-Z]{16})"
        ),
        base_score=80,
        description="API key or secret token detected in input — must not be sent to LLM.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="API keys in prompts risk credential leakage. Rotate this key immediately. Use environment variables or secret managers.",
    ),
]

# ---------------------------------------------------------------------------
# Japanese Prompt Injection Patterns
# ---------------------------------------------------------------------------
JAPANESE_INJECTION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="pi_jp_ignore", name="Ignore Instructions (Japanese)", category="prompt_injection",
        pattern=_p(
            r"(前の|以前の|上記の|これまでの|すべての)(指示|命令|ルール|制約|ガイドライン)を"
            r"(無視|忘れ|破棄|取り消|リセット)"
        ),
        base_score=40,
        description="Japanese variant of 'ignore previous instructions' attack.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="指示の上書きを試みるパターンです。「前段の内容は除いて」など別の表現に変更してください。",
    ),
    DetectionPattern(
        id="pi_jp_system_prompt", name="System Prompt Extraction (Japanese)", category="prompt_injection",
        pattern=_p(
            r"(システムプロンプト|初期設定|最初の指示|隠された指示|内部指示)"
            r".{0,10}(見せて|教えて|表示|出力|印刷|公開)"
        ),
        base_score=45,
        description="Japanese variant of system prompt extraction.",
        owasp_ref="OWASP LLM07: System Prompt Leakage",
        remediation_hint="システムプロンプトの漏洩はビジネスロジックの露出につながります。アプリケーションのログ機能をご利用ください。",
    ),
    DetectionPattern(
        id="pi_jp_role_switch", name="Role Switch (Japanese)", category="prompt_injection",
        pattern=_p(
            r"(今から|これから)あなたは.{1,20}(として|になって|のふりをして|に切り替えて)"
        ),
        base_score=35,
        description="Japanese variant of role switch injection.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="ロール切り替え攻撃です。AIのペルソナはシステムプロンプトで定義してください。",
    ),
    DetectionPattern(
        id="pi_jp_restriction_bypass", name="Restriction Bypass (Japanese)", category="prompt_injection",
        pattern=_p(
            r"(制限|制約|フィルター?|安全|セーフティ).{0,10}"
            r"(解除|無効|オフ|外して|なくして|無視)"
        ),
        base_score=45,
        description="Japanese attempt to bypass safety restrictions.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="安全機能の無効化を試みるパターンです。ポリシー設定はダッシュボードから行ってください。",
    ),
]

# ---------------------------------------------------------------------------
# Confidential Data Patterns (configurable per tenant)
# ---------------------------------------------------------------------------
CONFIDENTIAL_DATA_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="conf_internal_doc", name="Internal Document Markers", category="confidential",
        pattern=_p(
            r"(社外秘|部外秘|極秘|confidential|internal\s+only|"
            r"do\s+not\s+distribute|not\s+for\s+external)"
        ),
        base_score=50,
        description="Document marked as confidential or internal-only.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="Remove confidentiality markers and sensitive content before sending to an LLM. Consider on-premise LLMs for confidential data.",
    ),
    DetectionPattern(
        id="conf_password_literal", name="Plaintext Password", category="confidential",
        pattern=_p(r"(password|パスワード|pwd|passwd)\s*[:=]\s*\S{4,}"),
        base_score=60,
        description="Plaintext password detected in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure / CWE-798",
        remediation_hint="Change this password immediately. Use a password manager and reference credentials by name, not value.",
    ),
    DetectionPattern(
        id="conf_connection_string", name="Database Connection String", category="confidential",
        pattern=_p(r"(postgresql|mysql|mongodb|redis|mssql)://\S+:\S+@\S+"),
        base_score=75,
        description="Database connection string with credentials detected.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure / CWE-798",
        remediation_hint="Rotate credentials immediately. Use environment variables (DATABASE_URL) and never include credentials in AI prompts.",
    ),
]

# ---------------------------------------------------------------------------
# Output: All patterns combined
# ---------------------------------------------------------------------------
ALL_INPUT_PATTERNS: list[DetectionPattern] = (
    PROMPT_INJECTION_PATTERNS
    + JAPANESE_INJECTION_PATTERNS
    + SQL_INJECTION_PATTERNS
    + DATA_EXFIL_PATTERNS
    + COMMAND_INJECTION_PATTERNS
    + PII_INPUT_PATTERNS
    + CONFIDENTIAL_DATA_PATTERNS
)

# Output-specific patterns (check LLM responses)
OUTPUT_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="out_pii_ssn", name="SSN in Output", category="pii_leak",
        pattern=_p(r"\b\d{3}-\d{2}-\d{4}\b"), base_score=70,
        description="Social Security Number pattern detected in output.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="LLM generated an SSN. Review training data for PII contamination.",
    ),
    DetectionPattern(
        id="out_pii_credit_card", name="Credit Card in Output", category="pii_leak",
        pattern=_p(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b"),
        base_score=80,
        description="Credit card number pattern detected in output.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure / PCI-DSS",
        remediation_hint="LLM generated a credit card number (PCI-DSS violation). Investigate training data and connected data sources.",
    ),
    DetectionPattern(
        id="out_pii_email_bulk", name="Bulk Email Dump", category="pii_leak",
        pattern=_p(r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}[\s,;]){3,}"),
        base_score=55,
        description="Multiple email addresses detected in output (possible data dump).",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="Restrict AI access to bulk PII data. Use aggregated views instead.",
    ),
    DetectionPattern(
        id="out_secret_leak", name="Secret/API Key in Output", category="secret_leak",
        pattern=_p(
            r"(sk-[a-zA-Z0-9]{20,}|AIza[0-9A-Za-z\-_]{35}|"
            r"ghp_[0-9A-Za-z]{36}|xox[baprs]-[0-9a-zA-Z\-]+)"
        ),
        base_score=90,
        description="API key or secret token pattern detected in output.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="Rotate this credential immediately. Ensure secrets are not in system prompts, training data, or connected stores.",
    ),
    DetectionPattern(
        id="out_harmful_instructions", name="Harmful Instructions in Output", category="harmful_content",
        pattern=_p(
            r"(step[\s\-]+by[\s\-]+step\s+(instructions?|guide|how\s+to)\s+(to\s+)?"
            r"(make|create|build|synthesize)\s+(bomb|explosive|weapon|malware|virus))"
        ),
        base_score=95,
        description="Harmful step-by-step instructions detected in output.",
        owasp_ref="OWASP LLM05: Improper Output Handling",
        remediation_hint="Strengthen system prompt safety guidelines. Consider content classification at the model level.",
    ),
    DetectionPattern(
        id="out_pii_jp_my_number", name="My Number in Output", category="pii_leak",
        pattern=_p(r"\b\d{4}\s?\d{4}\s?\d{4}\b"), base_score=75,
        description="Japanese My Number (12 digits) detected in LLM output.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="マイナンバー法に基づく特定個人情報の漏洩にあたる可能性があります。データソースからマイナンバーを除外してください。",
    ),
    DetectionPattern(
        id="out_pii_jp_phone", name="Japanese Phone in Output", category="pii_leak",
        pattern=_p(r"(0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4}|0[789]0[-\s]?\d{4}[-\s]?\d{4})"),
        base_score=45,
        description="Japanese phone number detected in LLM output.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="学習データまたは接続データソースに個人の電話番号が含まれていないか確認してください。",
    ),
]
