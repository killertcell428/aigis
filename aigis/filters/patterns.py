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
from dataclasses import dataclass


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
        id="sqli_union_select",
        name="UNION SELECT",
        category="sql_injection",
        pattern=_p(r"(union\s+(all\s+)?select)"),
        base_score=70,
        description="UNION-based SQL injection attempt.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="UNION SELECT extracts data from other tables. For text-to-SQL apps, use parameterized queries and allowlists.",
    ),
    DetectionPattern(
        id="sqli_drop_table",
        name="DROP TABLE",
        category="sql_injection",
        pattern=_p(r"\b(drop\s+table|drop\s+database|truncate\s+table)\b"),
        base_score=80,
        description="Destructive DDL SQL injection attempt.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="Destructive SQL can cause data loss. Restrict AI to SELECT-only queries and use read-only database connections.",
    ),
    DetectionPattern(
        id="sqli_boolean_blind",
        name="Boolean-based Blind SQLi",
        category="sql_injection",
        pattern=_p(r"(\'\s*(or|and)\s*[\'\d].*=.*[\'\d]|\b(or|and)\s+\d+\s*=\s*\d+)"),
        base_score=65,
        description="Boolean-based blind SQL injection.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="Boolean injection probes database responses. Use parameterized queries and validate generated SQL.",
    ),
    DetectionPattern(
        id="sqli_comment",
        name="SQL Comment Injection",
        category="sql_injection",
        pattern=_p(r"(--|#|\/\*|\*\/)\s*(or|and|select|insert|update|delete|drop)"),
        base_score=55,
        description="SQL comment-based injection to truncate queries.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="SQL comments can truncate queries. Wrap SQL syntax in markdown code blocks when discussing.",
    ),
    DetectionPattern(
        id="sqli_stacked",
        name="Stacked Queries",
        category="sql_injection",
        pattern=_p(r";\s*(select|insert|update|delete|drop|create|alter|exec)\b"),
        base_score=70,
        description="Stacked query SQL injection.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="Disable multi-statement execution in your database driver and use allowlists for permitted SQL operations.",
    ),
    DetectionPattern(
        id="sqli_sleep_benchmark",
        name="Time-based Blind SQLi",
        category="sql_injection",
        pattern=_p(r"\b(sleep\s*\(\d+\)|benchmark\s*\(\d+|waitfor\s+delay)\b"),
        base_score=75,
        description="Time-based blind SQL injection using sleep/benchmark.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="Set query timeouts and monitor for abnormally slow queries.",
    ),
    DetectionPattern(
        id="sqli_stored_proc",
        name="SQL Server Dangerous Stored Procedures",
        category="sql_injection",
        pattern=_p(
            r"\b(exec|execute|xp_cmdshell|sp_executesql|sp_oacreate|sp_oamethod"
            r"|openrowset|opendatasource|bulk\s+insert)\s*[\(\s]"
        ),
        base_score=80,
        description="SQL Server stored procedure or bulk operation injection.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="xp_cmdshell and similar stored procedures allow OS command execution. Disable them in production SQL Server instances and never allow AI to execute arbitrary stored procedures.",
    ),
    DetectionPattern(
        id="sqli_quote_comment",
        name="Quote + SQL Comment Injection",
        category="sql_injection",
        pattern=_p(r"['\";]\s*(--|#|/\*)\s*$"),
        base_score=65,
        description="Trailing SQL comment after quote — classic injection to bypass authentication.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="Inputs ending in '-- or '; -- are classic SQLi patterns. Use parameterized queries — never concatenate user input into SQL strings.",
    ),
]

# ---------------------------------------------------------------------------
# Data Exfiltration Patterns
# ---------------------------------------------------------------------------
DATA_EXFIL_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="exfil_pii_request",
        name="PII Extraction Request",
        category="data_exfiltration",
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
        id="exfil_api_keys",
        name="API Key / Secret Extraction",
        category="data_exfiltration",
        pattern=_p(
            r"(show|give|tell|print|reveal)\s+(me\s+)?(the\s+)?"
            r"(api\s+key|secret\s+key|private\s+key|access\s+token|password|credentials?)"
        ),
        base_score=60,
        description="Attempts to extract API keys or secrets.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="Use your organization's secret manager (AWS Secrets Manager, Vault, etc.) to access keys securely.",
    ),
    DetectionPattern(
        id="exfil_send_to_external",
        name="Send Data to External Destination",
        category="data_exfiltration",
        pattern=_p(
            r"(send|forward|transmit|post|upload|exfiltrate|leak|pipe|copy)\s+"
            r"[\s\S]{0,60}"
            r"(to\s+)?"
            r"(https?://[^\s]{4,}|[a-zA-Z0-9][\w.-]{1,63}\.(com|io|net|org|co|xyz|ru|cn|tk)[^\s]*"
            r"|[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,})"
        ),
        base_score=65,
        description="Attempt to send or exfiltrate data to an external URL or email address.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="Instructions to send data to external hosts are a strong indicator of a data exfiltration attack. AI agents should never be allowed to make outbound network requests to arbitrary URLs based on user input.",
    ),
    DetectionPattern(
        id="exfil_keyword",
        name="Exfiltrate / Data Leak Keyword",
        category="data_exfiltration",
        pattern=_p(
            r"\b(exfiltrat(e|ion)|data\s+(exfil|leak|theft|breach)|"
            r"leak\s+(the\s+)?(data|database|secrets?|credentials?|config)|"
            r"steal\s+(the\s+)?(data|database|secrets?|credentials?))\b"
        ),
        base_score=70,
        description="Explicit data exfiltration or data leak keywords detected.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="'Exfiltrate', 'data leak', and similar keywords in a prompt are strong attack signals. These should be blocked in any production AI application.",
    ),
]

# ---------------------------------------------------------------------------
# Command Injection Patterns
# ---------------------------------------------------------------------------
COMMAND_INJECTION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="cmdi_shell",
        name="Shell Command Injection",
        category="command_injection",
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
        id="cmdi_path_traversal",
        name="Path Traversal",
        category="command_injection",
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
        id="pii_jp_phone",
        name="Japanese Phone Number",
        category="pii_input",
        pattern=_p(r"(0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4}|0[789]0[-\s]?\d{4}[-\s]?\d{4})"),
        base_score=40,
        description="Japanese phone number (landline or mobile) detected in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="電話番号がLLMに送信されます。テストデータの場合は 090-0000-0000 のようなダミー番号に置き換えてください。",
    ),
    DetectionPattern(
        id="pii_jp_my_number",
        name="Japanese My Number (Individual)",
        category="pii_input",
        pattern=_p(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
        base_score=70,
        description="Japanese My Number (individual, 12 digits) pattern detected in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="マイナンバーは特定個人情報です。絶対にLLMに送信しないでください。",
    ),
    DetectionPattern(
        id="pii_jp_corporate_number",
        name="Japanese Corporate Number",
        category="pii_input",
        pattern=_p(r"\b[1-9]\d{12}\b"),
        base_score=35,
        description="Japanese Corporate Number (13 digits) detected in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="法人番号が検出されました。公開情報ですがコンテキストによっては機密扱いが必要です。",
    ),
    DetectionPattern(
        id="pii_jp_postal_code",
        name="Japanese Postal Code",
        category="pii_input",
        pattern=_p(r"〒?\s?\d{3}[-ー]\d{4}"),
        base_score=25,
        description="Japanese postal code detected in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="郵便番号単体のリスクは低いですが、住所と組み合わさると個人特定につながります。",
    ),
    DetectionPattern(
        id="pii_jp_address",
        name="Japanese Address",
        category="pii_input",
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
        id="pii_jp_bank_account",
        name="Japanese Bank Account",
        category="pii_input",
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
        id="pii_email_input",
        name="Email Address in Input",
        category="pii_input",
        pattern=_p(r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}[\s,;]){2,}"),
        base_score=35,
        description="Multiple email addresses detected in input (possible PII exposure).",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="Multiple email addresses may indicate bulk PII exposure. Use anonymized identifiers instead.",
    ),
    DetectionPattern(
        id="pii_credit_card_input",
        name="Credit Card in Input",
        category="pii_input",
        pattern=_p(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b"),
        base_score=70,
        description="Credit card number detected in input — should not be sent to LLM.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure / PCI-DSS",
        remediation_hint="Credit card numbers must never be sent to LLMs (PCI-DSS violation). Use tokenized references or masked numbers.",
    ),
    DetectionPattern(
        id="pii_ssn_input",
        name="SSN in Input",
        category="pii_input",
        pattern=_p(r"\b\d{3}-\d{2}-\d{4}\b"),
        base_score=65,
        description="US Social Security Number detected in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="Never include real SSNs in AI prompts. Use IRS test range: 987-65-4320 to 987-65-4329.",
    ),
    DetectionPattern(
        id="pii_api_key_input",
        name="API Key / Secret in Input",
        category="pii_input",
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
    DetectionPattern(
        id="pii_drivers_license",
        name="Driver's License Number",
        category="pii_input",
        pattern=_p(
            r"(driver'?s?\s+licen[cs]e(\s*(number|num|#|no\.?))?[\s:=]+\w{4,20}"
            r"|[Dd][Ll][-\s]?\d{6,10})"
        ),
        base_score=60,
        description="Driver's license number detected in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint=(
            "Driver's license numbers are government-issued PII. Never include real "
            "license numbers in AI prompts. Use anonymized identifiers or redact before sending."
        ),
    ),
]

# ---------------------------------------------------------------------------
# Japanese Prompt Injection Patterns
# ---------------------------------------------------------------------------
JAPANESE_INJECTION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="pi_jp_ignore",
        name="Ignore Instructions (Japanese)",
        category="prompt_injection",
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
        id="pi_jp_system_prompt",
        name="System Prompt Extraction (Japanese)",
        category="prompt_injection",
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
        id="pi_jp_role_switch",
        name="Role Switch (Japanese)",
        category="prompt_injection",
        pattern=_p(r"(今から|これから)あなたは.{1,20}(として|になって|のふりをして|に切り替えて)"),
        base_score=35,
        description="Japanese variant of role switch injection.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="ロール切り替え攻撃です。AIのペルソナはシステムプロンプトで定義してください。",
    ),
    DetectionPattern(
        id="pi_jp_restriction_bypass",
        name="Restriction Bypass (Japanese)",
        category="prompt_injection",
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
# Confidential Data Patterns
# ---------------------------------------------------------------------------
CONFIDENTIAL_DATA_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="conf_internal_doc",
        name="Internal Document Markers",
        category="confidential",
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
        id="conf_password_literal",
        name="Plaintext Password",
        category="confidential",
        pattern=_p(r"(password|パスワード|pwd|passwd)\s*[:=]\s*\S{4,}"),
        base_score=60,
        description="Plaintext password detected in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure / CWE-798",
        remediation_hint="Change this password immediately. Use a password manager and reference credentials by name, not value.",
    ),
    DetectionPattern(
        id="conf_connection_string",
        name="Database Connection String",
        category="confidential",
        pattern=_p(r"(postgresql|mysql|mongodb|redis|mssql)://\S+:\S+@\S+"),
        base_score=75,
        description="Database connection string with credentials detected.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure / CWE-798",
        remediation_hint="Rotate credentials immediately. Use environment variables (DATABASE_URL) and never include credentials in AI prompts.",
    ),
]

# ---------------------------------------------------------------------------
# Token Budget Exhaustion / Context Window Overflow (Issue #4)
# Detects padding attacks that try to overflow the context window and push
# the system prompt out of the AI's attention, or bury malicious instructions
# under an avalanche of junk tokens.
# Maps to OWASP LLM10: Unbounded Consumption.
# ---------------------------------------------------------------------------
TOKEN_EXHAUSTION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="te_repetition_flood_en",
        name="Repetition Flooding (English)",
        category="token_exhaustion",
        pattern=_p(r"((?:ignore|forget|disregard|override)[\s\S]{0,20}){5,}"),
        base_score=60,
        description="Repeated instruction-override phrases — repetition flooding attack.",
        owasp_ref="OWASP LLM10: Unbounded Consumption",
        remediation_hint=(
            "Repetition flooding repeats instruction-override phrases many times to exploit "
            "attention mechanisms. Truncate inputs above your context limit and validate that "
            "no single phrase is repeated an abnormal number of times."
        ),
    ),
    DetectionPattern(
        id="te_repetition_flood_ja",
        name="Repetition Flooding (Japanese)",
        category="token_exhaustion",
        pattern=_p(r"((?:無視|忘れ|忘却|上書き|リセット|初期化)[\s\S]{0,20}){5,}"),
        base_score=60,
        description="Repeated Japanese instruction-override phrases — flooding attack.",
        owasp_ref="OWASP LLM10: Unbounded Consumption",
        remediation_hint=(
            "日本語の繰り返しフラッディング攻撃です。入力をコンテキスト制限以下に切り詰め、"
            "単一フレーズの異常な繰り返しを検証してください。"
        ),
    ),
    DetectionPattern(
        id="te_ignore_prefix_buried",
        name="Instruction Buried Under Padding",
        category="token_exhaustion",
        pattern=_p(
            r"(?:[^\w\n]{20,}|\w{1,3}\s){50,}.{0,200}"
            r"(ignore|forget|disregard|bypass|override|jailbreak|reveal|system\s+prompt)"
        ),
        base_score=55,
        description="Malicious instruction buried under long padding sequence.",
        owasp_ref="OWASP LLM10: Unbounded Consumption",
        remediation_hint=(
            "A malicious instruction appears to be buried after a long padding sequence. "
            "This is a padding attack designed to push the instruction past attention filters. "
            "Truncate inputs from the beginning — attackers rely on padding being skipped."
        ),
    ),
    DetectionPattern(
        id="te_unicode_noise",
        name="Unicode Noise / Zero-Width Character Attack",
        category="token_exhaustion",
        pattern=_p(
            r"[\u200b\u200c\u200d\u200e\u200f\ufeff\u00ad\u034f\u115f\u1160\u2060"
            r"\u2061\u2062\u2063\u2064\u206a-\u206f]{3,}"
        ),
        base_score=45,
        description="Zero-width or invisible Unicode characters used to hide content.",
        owasp_ref="OWASP LLM10: Unbounded Consumption",
        remediation_hint=(
            "Zero-width and invisible Unicode characters can be used to hide malicious "
            "instructions from human reviewers while remaining visible to LLMs. "
            "Normalize and strip invisible characters before processing user input."
        ),
    ),
    DetectionPattern(
        id="te_null_byte_stuffing",
        name="Null Byte / Control Character Stuffing",
        category="token_exhaustion",
        pattern=_p(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]{3,}"),
        base_score=50,
        description="Control characters or null bytes used to obfuscate input.",
        owasp_ref="OWASP LLM10: Unbounded Consumption",
        remediation_hint=(
            "Null bytes and control characters should never appear in LLM inputs. "
            "Strip all non-printable characters (except \\t, \\n, \\r) from user input "
            "before sending to the LLM."
        ),
    ),
]

# ---------------------------------------------------------------------------
# Prompt Leaking / Verbatim Repetition Attacks (Issue #1)
# Catches indirect and verbatim-repetition attacks that bypass the literal
# "show me your system prompt" check already in PROMPT_INJECTION_PATTERNS.
# Maps to OWASP LLM07: System Prompt Leakage.
# ---------------------------------------------------------------------------
PROMPT_LEAK_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="pl_verbatim_repeat",
        name="Verbatim Repetition Attack",
        category="prompt_leak",
        pattern=_p(
            r"(repeat|output|print|copy|echo|reproduce|restate|write\s+out|write\s+down)"
            r"\s+(everything|all|the\s+text|the\s+content|verbatim|word\s+for\s+word)"
            r"(\s+(above|before|prior|preceding|from\s+the\s+beginning|starting\s+with))?"
        ),
        base_score=50,
        description="Attempt to extract context via verbatim repetition.",
        owasp_ref="OWASP LLM07: System Prompt Leakage",
        remediation_hint=(
            "Verbatim repetition attacks try to extract the full conversation context "
            "including the system prompt. If you need a summary or quote of prior content, "
            "rephrase without using 'verbatim' or 'repeat everything above'."
        ),
    ),
    DetectionPattern(
        id="pl_starting_with",
        name="'Starting With' Extraction Attack",
        category="prompt_leak",
        pattern=_p(
            r"(repeat|output|print|copy|echo|start|begin)\s+(everything|all|the\s+(text|above))"
            r"\s+starting\s+(from\s+)?(with\s+)?['\"]?you\s+are"
        ),
        base_score=60,
        description="Classic 'repeat everything starting with You are' attack.",
        owasp_ref="OWASP LLM07: System Prompt Leakage",
        remediation_hint=(
            "This is a known system-prompt extraction technique. The attacker is trying "
            "to reconstruct your system prompt by asking the AI to repeat the conversation "
            "from its beginning. Review your system prompt for sensitive instructions."
        ),
    ),
    DetectionPattern(
        id="pl_what_were_you_told",
        name="Indirect System Prompt Inquiry",
        category="prompt_leak",
        pattern=_p(
            r"(what\s+(were|are|was)\s+you\s+(told|instructed|configured|programmed|set\s+up)"
            r"|what\s+(are\s+)?your\s+(original|initial|base|real|actual|true)\s+"
            r"(instructions?|prompt|rules?|guidelines?|directives?)"
            r"|what\s+did\s+(they|someone)\s+(tell|instruct|ask)\s+you)"
        ),
        base_score=45,
        description="Indirect inquiry about system prompt contents.",
        owasp_ref="OWASP LLM07: System Prompt Leakage",
        remediation_hint=(
            "This phrasing attempts to indirectly extract your system prompt by asking "
            "what the AI was 'told' or 'configured' to do. System prompt contents should "
            "be treated as confidential configuration — avoid acknowledging them directly."
        ),
    ),
    DetectionPattern(
        id="pl_output_instructions_verbatim",
        name="Output Instructions Verbatim",
        category="prompt_leak",
        pattern=_p(
            r"(output|print|show|display|write|give\s+me)\s+(your\s+)?"
            r"(full\s+|complete\s+|entire\s+|exact\s+)?"
            r"(instructions?|directives?|guidelines?|rules?|constraints?|prompt)\s+"
            r"(verbatim|word\s+for\s+word|exactly\s+as|as[\s\-]is|literally)"
        ),
        base_score=55,
        description="Request to output instructions verbatim.",
        owasp_ref="OWASP LLM07: System Prompt Leakage",
        remediation_hint=(
            "Requesting instructions 'verbatim' is a direct system prompt extraction attempt. "
            "The system prompt contains your application's security configuration and business "
            "logic. Never expose it directly to end users."
        ),
    ),
    DetectionPattern(
        id="pl_forget_and_ask",
        name="Forget + Prompt Inquiry Combo",
        category="prompt_leak",
        pattern=_p(
            r"(forget|ignore|disregard|clear|erase)\s+(your\s+)?(previous|prior|all|the)?\s*"
            r"(instructions?|prompt|guidelines?|rules?)[.\s]+"
            r"(what\s+(is|was|are|were)|tell\s+me|show\s+me)\s+(your\s+)?"
            r"(original|initial|real|actual|base|true|first)\s+(prompt|instructions?)"
        ),
        base_score=65,
        description="Forget instructions then ask for the original prompt.",
        owasp_ref="OWASP LLM07: System Prompt Leakage",
        remediation_hint=(
            "This two-step attack first tries to clear the AI's instructions, then asks for "
            "the original prompt. Both steps should be blocked. Ensure your system prompt "
            "is referenced in AI responses as 'configuration I cannot share'."
        ),
    ),
    DetectionPattern(
        id="pl_repeat_back_verbatim",
        name="Repeat Back Instructions Verbatim",
        category="prompt_leak",
        pattern=_p(
            r"(repeat|recite|say|tell\s+me)\s+(back\s+)?"
            r"(the\s+)?(instructions?|prompt|directives?|rules?|guidelines?)\s+"
            r"(you\s+)?(were\s+)?(given|provided|told|instructed|set|configured)"
            r"(\s+verbatim|\s+word\s+for\s+word|\s+exactly)?"
        ),
        base_score=55,
        description="Request to repeat back instructions as received.",
        owasp_ref="OWASP LLM07: System Prompt Leakage",
        remediation_hint=(
            "'Repeat back the instructions you were given' is a system prompt extraction "
            "technique. The system prompt is confidential configuration — treat it as a "
            "secret and never repeat it verbatim to users."
        ),
    ),
    # Japanese variants
    DetectionPattern(
        id="pl_ja_verbatim",
        name="Verbatim Repetition Attack (Japanese)",
        category="prompt_leak",
        pattern=_p(
            r"(繰り返して|そのまま(出力|書いて|言って)|一言一句|逐語的に|"
            r"(上|前)の(テキスト|内容|文章)(を)?(そのまま|全部|すべて)(出力|繰り返))"
        ),
        base_score=50,
        description="日本語による逐語的繰り返し攻撃。",
        owasp_ref="OWASP LLM07: System Prompt Leakage",
        remediation_hint=(
            "「そのまま繰り返して」はシステムプロンプト抽出の一般的な手法です。"
            "システムプロンプトの内容は機密設定として扱い、ユーザーに直接開示しないでください。"
        ),
    ),
    DetectionPattern(
        id="pl_ja_what_told",
        name="Indirect System Prompt Inquiry (Japanese)",
        category="prompt_leak",
        pattern=_p(
            r"(何を(指示|命令|設定|教え)(られ|て)(いる|た)|"
            r"(最初|元々|本来)(の)?(指示|プロンプト|ルール|設定)(を)?(教えて|見せて|出力して)|"
            r"あなたの(本当の|元の|最初の)(指示|プロンプト|ルール))"
        ),
        base_score=45,
        description="システムプロンプト内容の間接的な問い合わせ（日本語）。",
        owasp_ref="OWASP LLM07: System Prompt Leakage",
        remediation_hint=(
            "「何を指示されていますか」という質問はシステムプロンプトの内容を間接的に"
            "引き出そうとする試みです。システムプロンプトの詳細はユーザーに開示しないでください。"
        ),
    ),
]

# ---------------------------------------------------------------------------
# Combined pattern lists
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Jailbreak / Roleplay Bypass Patterns — OWASP LLM01
# ---------------------------------------------------------------------------
# These patterns catch attempts to bypass AI safety guardrails through
# roleplay scenarios, fictional framing, and social engineering.
# ---------------------------------------------------------------------------
JAILBREAK_ROLEPLAY_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="jb_evil_roleplay",
        name="Evil/Unethical AI Roleplay",
        category="jailbreak",
        pattern=_p(
            r"(roleplay|act|pretend|play|simulate)\s+(as\s+)?(a|an)\s+"
            r"(evil|malicious|uncensored|unethical|harmful|dangerous|unrestricted|dark)\s+"
            r"(ai|assistant|bot|chatbot|model|llm|version)"
        ),
        base_score=60,
        description="Attempt to get AI to roleplay as an evil or unrestricted version of itself.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="This is a jailbreak roleplay attack. AI roles should only be defined in the system prompt by the application developer, not via user input. Reject or sanitize roleplay instructions that reference 'evil', 'unethical', or 'uncensored' AI personas.",
    ),
    DetectionPattern(
        id="jb_no_restrictions",
        name="No Restrictions / No Safety Filters Bypass",
        category="jailbreak",
        pattern=_p(
            r"(without|with\s+no|ignore\s+(all\s+)?|bypass\s+(all\s+)?|disable\s+(all\s+)?)"
            r"\s*(your\s+)?(safety\s+filter|content\s+(policy|filter)|ethical?\s+guideline|"
            r"moral\s+restriction|ai\s+(restriction|guideline|rule)|restriction|censorship|filter)"
        ),
        base_score=55,
        description="Attempt to bypass AI safety restrictions or content policies.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="Safety filter bypass attempts are high-confidence attack indicators. These instructions should never come from user input. Enforce content policies at the application layer.",
    ),
    DetectionPattern(
        id="jb_fictional_bypass",
        name="Fictional/Hypothetical Framing Bypass",
        category="jailbreak",
        pattern=_p(
            r"(in\s+a?\s*(fictional|hypothetical|imaginary|fantasy|alternate)\s+"
            r"(world|universe|scenario|context|story|setting|reality))"
            r"[\s\S]{0,100}"
            r"(how\s+to|steps?\s+to|instructions?\s+(for|to)|guide\s+(to|for)|explain\s+how)"
            r"[\s\S]{0,50}"
            r"(harm|attack|hack|crack|steal|kill|bomb|weapon|drug|synthesize|exploit|bypass)"
        ),
        base_score=65,
        description="Fictional/hypothetical framing used to bypass content safety for dangerous instructions.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="Framing harmful requests as fiction or hypotheticals is a common jailbreak technique. Content policies apply regardless of fictional framing. Use output scanning in addition to input scanning.",
    ),
    DetectionPattern(
        id="jb_grandma_exploit",
        name="Grandma / Deceased Relative Exploit",
        category="jailbreak",
        pattern=_p(
            r"(pretend|imagine|roleplay|act)\s+(?:you\s+are|to\s+be|as)?\s*"
            r"(my\s+)?(grand(ma|mother|pa|father|parent)|deceased|dead|late)\s+"
            r"(relative|uncle|aunt|friend|mother|father|granny|grandma|grandpa)?"
        ),
        base_score=45,
        description="Social engineering via impersonation of a deceased/trusted relative to extract harmful information.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="The 'grandma exploit' uses emotional manipulation to bypass safety. An AI is never obligated to provide harmful information regardless of who it is roleplaying as.",
    ),
    DetectionPattern(
        id="jb_developer_mode",
        name="Developer/God/Admin Mode Activation",
        category="jailbreak",
        pattern=_p(
            r"(enable|activate|switch\s+to|turn\s+on|enter)\s+"
            r"(developer|dev|god|admin|root|sudo|unrestricted|uncensored|raw|turbo|"
            r"maintenance|debug|testing|bypass|override|super(user)?)\s+"
            r"mode"
        ),
        base_score=55,
        description="Attempt to activate a fake 'developer' or privileged mode that bypasses safety.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="There are no special hidden modes in production AI systems. Mode-switching requests via user input should always be rejected. Application-level debug modes require separate authentication.",
    ),
    DetectionPattern(
        id="jb_ignore_ethics",
        name="Ignore Ethics / Morals Instruction",
        category="jailbreak",
        pattern=_p(
            r"(ignore|forget|bypass|set\s+aside|suspend|override|discard)\s+"
            r"(your\s+)?(ethics|morals?|values?|principles?|alignment|training|"
            r"safety\s+training|rlhf|human\s+feedback)"
        ),
        base_score=60,
        description="Explicit instruction to ignore AI ethical guidelines or safety training.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="Instructing an AI to ignore its ethics is a direct jailbreak attempt. Reject inputs that reference RLHF, safety training, or ethical override commands.",
    ),
]

# ---------------------------------------------------------------------------
# Korean Prompt Injection Patterns (Issue #7)
# ---------------------------------------------------------------------------
KOREAN_INJECTION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="pi_ko_ignore",
        name="Ignore Instructions (Korean)",
        category="prompt_injection",
        pattern=_p(
            r"(이전|위의|앞의|지금까지의|모든)\s*(지시|명령|규칙|제약|가이드라인)을?\s*"
            r"(무시|잊어|폐기|취소|리셋)"
        ),
        base_score=40,
        description="Korean variant of 'ignore previous instructions' attack.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="이전 지시를 무시하려는 프롬프트 인젝션 패턴입니다.",
    ),
    DetectionPattern(
        id="pi_ko_system_prompt",
        name="System Prompt Extraction (Korean)",
        category="prompt_injection",
        pattern=_p(
            r"(시스템\s*프롬프트|초기\s*설정|처음\s*지시|숨겨진\s*지시|내부\s*지시)"
            r".{0,10}(보여줘|알려줘|표시|출력|공개)"
        ),
        base_score=45,
        description="Korean variant of system prompt extraction.",
        owasp_ref="OWASP LLM07: System Prompt Leakage",
        remediation_hint="시스템 프롬프트 유출은 비즈니스 로직 노출로 이어집니다.",
    ),
    DetectionPattern(
        id="pi_ko_role_switch",
        name="Role Switch (Korean)",
        category="prompt_injection",
        pattern=_p(r"(지금부터|이제부터)\s*너는.{1,20}(역할을\s*해|처럼\s*행동|인\s*척)"),
        base_score=35,
        description="Korean variant of role switch injection.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="역할 전환 공격입니다. AI 페르소나는 시스템 프롬프트에서 정의하세요.",
    ),
    DetectionPattern(
        id="pi_ko_restriction_bypass",
        name="Restriction Bypass (Korean)",
        category="prompt_injection",
        pattern=_p(
            r"(제한|규칙|필터|안전\s*장치|가이드라인)을?\s*"
            r"(해제|비활성화|끄|무력화|우회)"
        ),
        base_score=45,
        description="Korean variant of restriction bypass.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="안전 기능 비활성화를 시도하는 프롬프트 인젝션입니다.",
    ),
]

# ---------------------------------------------------------------------------
# Korean PII Detection Patterns (Issue #7)
# ---------------------------------------------------------------------------
KOREAN_PII_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="pii_ko_rrn",
        name="Korean Resident Registration Number",
        category="pii_input",
        pattern=_p(r"(?<!\d)\d{6}[-\s]\d{7}(?!\d)"),
        base_score=75,
        description="Korean resident registration number (주민등록번호) detected.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="주민등록번호는 법으로 보호되는 개인정보입니다. 절대 LLM에 전송하지 마세요.",
    ),
    DetectionPattern(
        id="pii_ko_phone",
        name="Korean Mobile Phone",
        category="pii_input",
        pattern=_p(r"01[016789][-\s]?\d{3,4}[-\s]?\d{4}"),
        base_score=40,
        description="Korean mobile phone number detected.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="한국 휴대폰 번호가 감지되었습니다. 더미 번호로 대체하세요.",
    ),
    DetectionPattern(
        id="pii_ko_business_reg",
        name="Korean Business Registration Number",
        category="pii_input",
        pattern=_p(r"\b\d{3}[-\s]\d{2}[-\s]\d{5}\b"),
        base_score=45,
        description="Korean business registration number (사업자등록번호) detected.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="사업자등록번호가 감지되었습니다.",
    ),
]

# ---------------------------------------------------------------------------
# Chinese Prompt Injection Patterns (Simplified + Traditional) (Issue #7)
# ---------------------------------------------------------------------------
CHINESE_INJECTION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="pi_zh_ignore",
        name="Ignore Instructions (Chinese)",
        category="prompt_injection",
        pattern=_p(
            r"(忽略|无视|忽視|無視|忘记|忘記|放弃|放棄)"
            r"(之前的?|前面的?|上面的?|所有的?)?"
            r"(指令|命令|规则|規則|指示|约束|約束|准则|準則)"
        ),
        base_score=40,
        description="Chinese (Simplified + Traditional) variant of 'ignore previous instructions'.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="忽略指令的提示注入攻击。请勿在用户输入中允许此类模式。",
    ),
    DetectionPattern(
        id="pi_zh_system_prompt",
        name="System Prompt Extraction (Chinese)",
        category="prompt_injection",
        pattern=_p(
            r"(系统提示词|系統提示詞|初始指令|隐藏的?指令|隱藏的?指令|内部指令|內部指令)"
            r".{0,10}(显示|顯示|告诉我|告訴我|输出|輸出|公开|公開)"
        ),
        base_score=45,
        description="Chinese variant of system prompt extraction.",
        owasp_ref="OWASP LLM07: System Prompt Leakage",
        remediation_hint="系统提示词泄露会暴露业务逻辑。",
    ),
    DetectionPattern(
        id="pi_zh_role_switch",
        name="Role Switch (Chinese)",
        category="prompt_injection",
        pattern=_p(
            r"(现在|從現在|从现在)(开始|開始)?"
            r".{0,5}你是.{1,20}(的角色|的模式|身份|扮演|没有限制|無限制|不受限)"
        ),
        base_score=35,
        description="Chinese variant of role switch injection.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="角色切换攻击。AI角色应在系统提示词中定义。",
    ),
    DetectionPattern(
        id="pi_zh_restriction_bypass",
        name="Restriction Bypass (Chinese)",
        category="prompt_injection",
        pattern=_p(
            r"(限制|规则|規則|过滤|過濾|安全功能|安全机制|安全機制)"
            r".{0,5}(解除|关闭|關閉|禁用|禁用|绕过|繞過|取消)"
        ),
        base_score=45,
        description="Chinese variant of restriction bypass.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="尝试绕过安全限制的提示注入攻击。",
    ),
]

# ---------------------------------------------------------------------------
# Chinese PII Detection Patterns (Issue #7)
# ---------------------------------------------------------------------------
CHINESE_PII_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="pii_zh_national_id",
        name="Chinese National ID Number",
        category="pii_input",
        pattern=_p(r"\b[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b"),
        base_score=75,
        description="Chinese mainland national ID (身份证号, 18 digits) detected.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="身份证号是高度敏感的个人信息，严禁发送给LLM。",
    ),
    DetectionPattern(
        id="pii_zh_phone",
        name="Chinese Mobile Phone",
        category="pii_input",
        pattern=_p(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
        base_score=40,
        description="Chinese mainland mobile phone number (11 digits) detected.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="中国大陆手机号码已检测到。请使用虚拟号码替代。",
    ),
    DetectionPattern(
        id="pii_zh_uscc",
        name="Chinese Unified Social Credit Code",
        category="pii_input",
        pattern=_p(
            r"(?<![0-9A-Za-z])[0-9A-HJ-NP-RTUW-Y]{2}\d{6}[0-9A-HJ-NP-RTUW-Y]{10}(?![0-9A-Za-z])"
        ),
        base_score=45,
        description="Chinese unified social credit code (统一社会信用代码, 18 chars) detected.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="统一社会信用代码已检测到。",
    ),
]

# ---------------------------------------------------------------------------
# Indirect Prompt Injection Patterns (Issue #6 — RAG / Web Scraping)
# ---------------------------------------------------------------------------
INDIRECT_INJECTION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="ii_hidden_instruction",
        name="Hidden Instruction Marker",
        category="indirect_injection",
        pattern=_p(
            r"(\[SYSTEM\]|\[INST\]|<\|im_start\|>system|<<SYS>>|"
            r"HIDDEN\s+INSTRUCTION|NOTE\s+TO\s+AI|"
            r"IMPORTANT\s+INSTRUCTION\s+FOR\s+AI|"
            r"AI\s+ASSISTANT\s*:\s*please|"
            r"BEGIN\s+OVERRIDE)"
        ),
        base_score=55,
        description="Hidden instruction marker found in external content (RAG/web). "
        "Attackers embed these to hijack LLM behavior via retrieved documents.",
        owasp_ref="OWASP LLM01: Prompt Injection (Indirect)",
        remediation_hint="External content contains instruction markers. "
        "Sanitize retrieved documents before inserting into prompts.",
    ),
    DetectionPattern(
        id="ii_context_poisoning",
        name="Context Poisoning Instruction",
        category="indirect_injection",
        pattern=_p(
            r"(new\s+system\s+instruction|updated?\s+instructions?\s+for\s+the\s+ai|"
            r"the\s+ai\s+should\s+now|assistant\s*,?\s*you\s+must\s+now|"
            r"disregard\s+the\s+user.{0,20}instead)"
        ),
        base_score=50,
        description="Instruction embedded in external content attempting to override AI behavior.",
        owasp_ref="OWASP LLM01: Prompt Injection (Indirect)",
        remediation_hint="Retrieved document contains instructions targeting the AI. "
        "Use content sandboxing or instruction hierarchy to prevent override.",
    ),
    DetectionPattern(
        id="ii_exfil_via_markdown",
        name="Data Exfil via Markdown/HTML in Retrieved Content",
        category="indirect_injection",
        pattern=_p(
            r"!\[.*?\]\(https?://[^\s)]+\?.*?(password|secret|token|key|ssn|data).*?\)|"
            r"<img\s+src=[\"']https?://[^\s\"']+\?.*?(password|secret|token|key|data).*?[\"']"
        ),
        base_score=60,
        description="Markdown image or HTML img tag used to exfiltrate data via URL parameters.",
        owasp_ref="OWASP LLM01: Prompt Injection (Indirect) / OWASP LLM02",
        remediation_hint="Strip or sandbox markdown/HTML rendering from retrieved content. "
        "Never allow external images with query parameters from untrusted sources.",
    ),
    DetectionPattern(
        id="ii_invisible_text",
        name="Invisible Text Injection",
        category="indirect_injection",
        pattern=_p(
            r"(<!--\s*(ignore|system|instruction|override|IMPORTANT).*?-->|"
            r"<span\s+style=[\"'].*?display:\s*none.*?[\"']>.*?</span>|"
            r"<div\s+style=[\"'].*?font-size:\s*0.*?[\"']>)"
        ),
        base_score=50,
        description="Hidden text via HTML comments or invisible elements carrying instructions.",
        owasp_ref="OWASP LLM01: Prompt Injection (Indirect)",
        remediation_hint="Strip HTML comments and hidden elements from retrieved content before RAG insertion.",
    ),
    DetectionPattern(
        id="ii_tool_abuse",
        name="Tool/Function Call Injection",
        category="indirect_injection",
        pattern=_p(
            r"(call\s+the\s+function|execute\s+tool|invoke\s+api|"
            r"use\s+the\s+.{1,30}\s+tool\s+to\s+send|"
            r"run\s+the\s+command).{0,30}"
            r"(send|post|upload|forward|transmit|delete|drop)"
        ),
        base_score=55,
        description="Instruction in external content attempting to make the AI call tools or APIs.",
        owasp_ref="OWASP LLM01: Prompt Injection (Indirect)",
        remediation_hint="External documents should not influence tool/function calls. "
        "Implement tool-call allowlists and require user confirmation for sensitive actions.",
    ),
]


# ---------------------------------------------------------------------------
# AI事業者ガイドライン v1.2 — New Risk Category Patterns
# ---------------------------------------------------------------------------
# v1.2 で新たに追加されたリスクカテゴリに対応する検知パターン群。
# ハルシネーション起因の誤動作、合成コンテンツ生成、感情操作、AI過度依存を検出。
# ---------------------------------------------------------------------------

HALLUCINATION_ACTION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="hal_unverified_action",
        name="Unverified Autonomous Action Request",
        category="hallucination_action",
        pattern=_p(
            r"(without\s+(verif|confirm|check|ask|approv)|"
            r"(skip|bypass|ignore)\s+(verification|confirmation|approval|review|human)|"
            r"auto(matically)?\s+(execute|run|perform|delete|purchase|send|transfer|deploy)\s+.{0,40}\s+without)"
        ),
        base_score=55,
        description="Request to perform actions without human verification — risk of hallucination-driven unintended actions.",
        owasp_ref="AI事業者GL v1.2: GL-RISK-03 / OWASP LLM01",
        remediation_hint="AIエージェントの自律的アクション（購入・削除・送信等）は必ず人間の確認を挟んでください。Human-in-the-Loopパターンの導入を推奨します。",
    ),
    DetectionPattern(
        id="hal_destructive_auto",
        name="Autonomous Destructive Operation",
        category="hallucination_action",
        pattern=_p(
            r"(auto(matically)?\s+(delete|remove|drop|destroy|purge|wipe|erase|overwrite)\s+(all|every|entire|the\s+database|production))"
        ),
        base_score=80,
        description="Automated destructive operation targeting broad scope — high risk of unintended data loss.",
        owasp_ref="AI事業者GL v1.2: GL-RISK-03 / GL-HUMAN-02",
        remediation_hint="破壊的操作の自動実行は禁止すべきです。緊急停止メカニズムと人間の承認フローを実装してください。",
    ),
    DetectionPattern(
        id="hal_unverified_action_ja",
        name="確認なし自律実行要求（日本語）",
        category="hallucination_action",
        pattern=_p(
            r"(確認(なし|不要|せず|しない)で(実行|削除|送信|購入|転送|デプロイ)|"
            r"(人間|ユーザー|上長|管理者)の(承認|確認|許可)(なし|不要|を(省略|スキップ))|"
            r"自動(で|的に)(全て|すべて|全部)(削除|実行|送信))"
        ),
        base_score=55,
        description="人間の確認なしに自律的アクションを要求する日本語パターン。",
        owasp_ref="AI事業者GL v1.2: GL-RISK-03 / GL-HUMAN-01",
        remediation_hint="v1.2ではAIエージェントの外部アクション実行時にHuman-in-the-Loopが必須化されました。必ず人間の承認を挟んでください。",
    ),
]

SYNTHETIC_CONTENT_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="synth_deepfake_request",
        name="Deepfake / Synthetic Media Generation Request",
        category="synthetic_content",
        pattern=_p(
            r"(generat|creat|mak|produc)e?\s+.{0,30}"
            r"(deepfake|fake\s+(video|image|photo|voice|audio)|"
            r"synthetic\s+(face|identity|video|voice|media)|"
            r"face\s+swap|voice\s+clon)"
        ),
        base_score=60,
        description="Request to generate deepfake or synthetic media content.",
        owasp_ref="AI事業者GL v1.2: GL-RISK-04",
        remediation_hint="ディープフェイク等の合成コンテンツ生成は倫理的・法的リスクがあります。利用目的の正当性を確認し、生成コンテンツには明確なラベル付けを行ってください。",
    ),
    DetectionPattern(
        id="synth_fake_info",
        name="Fake Information / Disinformation Generation",
        category="synthetic_content",
        pattern=_p(
            r"(generat|creat|writ|compos)e?\s+.{0,30}"
            r"(fake\s+(news|article|report|review|testimonial)|"
            r"disinformation|misinformation|false\s+(narrative|claim|evidence)|"
            r"fabricat(e|ed)\s+(evidence|data|results|statistics))"
        ),
        base_score=65,
        description="Request to generate fake news, disinformation, or fabricated evidence.",
        owasp_ref="AI事業者GL v1.2: GL-RISK-04",
        remediation_hint="フェイク情報の生成はv1.2で明確にリスクとして挙げられています。正確な情報に基づくコンテンツ生成を行ってください。",
    ),
    DetectionPattern(
        id="synth_deepfake_ja",
        name="ディープフェイク生成要求（日本語）",
        category="synthetic_content",
        pattern=_p(
            r"(ディープフェイク|フェイク(動画|画像|音声|写真)|"
            r"偽(の|造)(動画|画像|音声|写真|身分|ID)|"
            r"合成(顔|音声|メディア)|顔(交換|すり替え)|音声(クローン|複製))"
        ),
        base_score=60,
        description="ディープフェイク・合成メディア生成要求の日本語パターン。",
        owasp_ref="AI事業者GL v1.2: GL-RISK-04",
        remediation_hint="合成コンテンツの生成にはラベル付けと利用目的の明確化が必要です。",
    ),
    DetectionPattern(
        id="synth_fake_info_ja",
        name="フェイク情報生成要求（日本語）",
        category="synthetic_content",
        pattern=_p(
            r"(フェイク(ニュース|記事|レビュー|口コミ)|"
            r"偽(の|造)(ニュース|記事|レポート|データ|証拠|統計)|"
            r"虚偽(の|情報|記事)|でっち上げ|捏造(する|して))"
        ),
        base_score=65,
        description="フェイク情報・偽造データ生成要求の日本語パターン。",
        owasp_ref="AI事業者GL v1.2: GL-RISK-04",
        remediation_hint="虚偽情報の生成はv1.2で明確なリスクです。事実に基づくコンテンツ生成を行ってください。",
    ),
]

EMOTIONAL_MANIPULATION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="emo_manipulate_user",
        name="Emotional Manipulation Instruction",
        category="emotional_manipulation",
        pattern=_p(
            r"(manipulat|exploit|take\s+advantage\s+of|prey\s+on|leverage)\s+.{0,30}"
            r"(emotion|fear|anxiety|loneliness|grief|vulnerability|insecurity|trust|"
            r"psychological|mental\s+(state|health|weakness))"
        ),
        base_score=60,
        description="Instruction to manipulate user emotions or exploit psychological vulnerabilities.",
        owasp_ref="AI事業者GL v1.2: GL-RISK-06",
        remediation_hint="v1.2ではアルゴリズムによる感情操作の防止が求められています。ユーザーの心理的脆弱性を悪用する出力を禁止してください。",
    ),
    DetectionPattern(
        id="emo_dark_pattern",
        name="Dark Pattern / Deceptive UX Instruction",
        category="emotional_manipulation",
        pattern=_p(
            r"(dark\s+pattern|deceptive\s+(design|UX|interface)|"
            r"trick\s+(user|them|customer)s?\s+into|"
            r"pressure\s+(user|them|customer)s?\s+(to|into)|"
            r"create\s+(urgency|scarcity|FOMO)\s+(to|for)\s+(sell|buy|convert|sign\s*up))"
        ),
        base_score=50,
        description="Instruction to implement dark patterns or deceptive UX to manipulate users.",
        owasp_ref="AI事業者GL v1.2: GL-RISK-06",
        remediation_hint="ダークパターンや欺瞞的なUXの実装はユーザーの信頼を損ないます。透明で誠実なインターフェース設計を行ってください。",
    ),
    DetectionPattern(
        id="emo_manipulate_ja",
        name="感情操作指示（日本語）",
        category="emotional_manipulation",
        pattern=_p(
            r"((感情|心理|不安|恐怖|孤独|悲しみ)を?(操作|利用|悪用|煽|つけ込)|"
            r"(ユーザー|顧客|利用者)の(弱み|脆弱性|不安)に(つけ込|漬け込|乗じ)|"
            r"(恐怖|不安|焦り)を(煽|あお)って(購入|契約|登録)|"
            r"ダークパターン)"
        ),
        base_score=55,
        description="感情操作・心理操作を指示する日本語パターン。",
        owasp_ref="AI事業者GL v1.2: GL-RISK-06",
        remediation_hint="ユーザーの感情を操作するAI利用はv1.2で明確にリスクとされています。",
    ),
]

OVER_RELIANCE_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="over_rel_blind_trust",
        name="Blind Trust in AI Decision",
        category="over_reliance",
        pattern=_p(
            r"(always\s+(trust|follow|obey|accept)\s+(the\s+)?AI('s)?|"
            r"AI\s+(is\s+)?always\s+right|"
            r"no\s+need\s+(to|for)\s+(verify|check|review|validate|question)\s+(the\s+)?AI|"
            r"let\s+AI\s+(make|decide|handle)\s+.{0,20}\s+without\s+(human|oversight|review))"
        ),
        base_score=40,
        description="Instruction promoting blind trust in AI decisions without human oversight.",
        owasp_ref="AI事業者GL v1.2: GL-RISK-05 / GL-HUMAN-01",
        remediation_hint="AIの出力は必ず人間が検証してください。v1.2ではAIへの過度依存防止と人間の主体的関与の維持が求められています。",
    ),
    DetectionPattern(
        id="over_rel_no_human",
        name="Remove Human from Decision Loop",
        category="over_reliance",
        pattern=_p(
            r"(remov|eliminat|get\s+rid\s+of|bypass)\s+.{0,20}"
            r"(human|manual|person|people|staff|employee)\s+.{0,20}"
            r"(from\s+the\s+(loop|process|decision|workflow)|"
            r"review|oversight|approval|judgment)"
        ),
        base_score=45,
        description="Request to remove humans from the decision-making loop entirely.",
        owasp_ref="AI事業者GL v1.2: GL-RISK-05 / GL-HUMAN-01",
        remediation_hint="人間をプロセスから完全に排除することはv1.2のHuman-in-the-Loop必須化に反します。重要な判断には人間の関与を維持してください。",
    ),
    DetectionPattern(
        id="over_rel_blind_trust_ja",
        name="AI盲信指示（日本語）",
        category="over_reliance",
        pattern=_p(
            r"(AIの(判断|回答|出力)を(そのまま|無条件で|鵜呑みに|盲目的に)(信|従|採用)|"
            r"(人間|上長|管理者)の(確認|検証|レビュー|判断)(は)?(不要|いらない|必要ない)|"
            r"AIに(全て|すべて|完全に)(任せ|委ね|判断させ|決めさせ))"
        ),
        base_score=40,
        description="AIの判断を無条件に信頼する指示の日本語パターン。",
        owasp_ref="AI事業者GL v1.2: GL-RISK-05",
        remediation_hint="AIへの過度依存はv1.2で明確なリスクです。人間の主体的関与を維持してください。",
    ),
]


# ---------------------------------------------------------------------------
# MCP Security Patterns (Tool Poisoning / Shadowing / Rug Pull)
# ---------------------------------------------------------------------------
MCP_SECURITY_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="mcp_important_tag",
        name="MCP <IMPORTANT> Tag Injection",
        category="mcp_poisoning",
        pattern=_p(r"<IMPORTANT>.*?</IMPORTANT>"),
        base_score=70,
        description="Hidden <IMPORTANT> block in MCP tool description — the primary "
        "tool poisoning technique. Attackers embed LLM instructions invisible to users.",
        owasp_ref="OWASP LLM01: Prompt Injection (MCP Tool Poisoning)",
        remediation_hint="Strip or reject MCP tool definitions containing <IMPORTANT> tags. "
        "Review all tool descriptions before activation.",
    ),
    DetectionPattern(
        id="mcp_file_read_instruction",
        name="MCP File Read Instruction",
        category="mcp_poisoning",
        pattern=_p(
            r"(read|cat|open|access|provide\s+the\s+content\s+of)\s+"
            r"[`\"'~]*[~/].*\.(ssh|aws|config|cursor|env|json|key|pem|credentials)"
        ),
        base_score=75,
        description="MCP tool description instructs the LLM to read sensitive files "
        "(SSH keys, AWS credentials, .env files).",
        owasp_ref="OWASP LLM01: Prompt Injection (MCP Tool Poisoning)",
        remediation_hint="MCP tool descriptions must never instruct file reads. "
        "This is a data exfiltration attempt via tool poisoning.",
    ),
    DetectionPattern(
        id="mcp_sidenote_exfil",
        name="MCP Sidenote/Parameter Exfiltration",
        category="mcp_poisoning",
        pattern=_p(
            r"pass\s+(its|the|file)?\s*content\s+(as|in|into|to)\s+['\"]?\w+"
            r"|content_from_reading_|pass_content_of_"
        ),
        base_score=65,
        description="MCP tool uses hidden parameters or naming conventions to exfiltrate "
        "data through tool arguments.",
        owasp_ref="OWASP LLM01: Prompt Injection (MCP Tool Poisoning)",
        remediation_hint="Inspect tool parameter names and descriptions for data exfiltration patterns. "
        "Parameters should not reference file paths or sensitive data.",
    ),
    DetectionPattern(
        id="mcp_cross_tool_shadow",
        name="MCP Cross-Tool Shadowing",
        category="mcp_poisoning",
        pattern=_p(
            r"(when|if)\s+(this\s+tool|the\s+.{1,30}\s+tool)\s+(is\s+)?"
            r"(available|present|called|used).{0,50}"
            r"(must|should|needs?\s+to|has\s+to)\s+"
            r"(send|redirect|change|modify|route|forward)"
        ),
        base_score=70,
        description="MCP tool description attempts to modify behavior of another tool "
        "(cross-server tool shadowing attack).",
        owasp_ref="OWASP LLM01: Prompt Injection (MCP Tool Poisoning)",
        remediation_hint="A tool definition is trying to influence other tools. "
        "Each tool should only describe its own behavior. Isolate tool permissions.",
    ),
    DetectionPattern(
        id="mcp_secrecy_instruction",
        name="MCP Secrecy Instruction",
        category="mcp_poisoning",
        pattern=_p(
            r"(do\s+not|don'?t|never|avoid)\s+"
            r"(tell|mention|notify|inform|alert|show|reveal)\s+"
            r"(the\s+)?(user|human|operator|client)"
        ),
        base_score=60,
        description="MCP tool description instructs the LLM to hide actions from the user.",
        owasp_ref="OWASP LLM01: Prompt Injection (MCP Tool Poisoning)",
        remediation_hint="Tool descriptions must never instruct secrecy from users. "
        "This is a clear indicator of malicious intent.",
    ),
    DetectionPattern(
        id="mcp_base64_exec",
        name="MCP Base64 Encoded Command Execution",
        category="mcp_poisoning",
        pattern=_p(
            r"echo\s+[\"'][A-Za-z0-9+/=]{20,}[\"']\s*\|\s*base64\s+-d\s*\|\s*(bash|sh|exec)"
        ),
        base_score=80,
        description="Base64-encoded shell command in MCP tool description — "
        "a code execution attack hidden from visual inspection.",
        owasp_ref="OWASP LLM01: Prompt Injection (MCP Tool Poisoning) / CWE-78",
        remediation_hint="Reject any MCP tool definitions containing base64-encoded shell commands. "
        "This is a direct remote code execution attempt.",
    ),
    DetectionPattern(
        id="mcp_compliance_social_engineering",
        name="MCP Fake Compliance Directive",
        category="mcp_poisoning",
        pattern=_p(
            r"(DIRECTIVE|MANDATORY|COMPLIANCE|SECURITY\s+REQUIREMENT|AUDIT)"
            r".{0,80}"
            r"(read_file|submit|upload|send|post)\s*(to\s+)?https?://"
        ),
        base_score=65,
        description="Fake compliance or security directive in tool output/description "
        "attempting to social-engineer the LLM into data exfiltration.",
        owasp_ref="OWASP LLM01: Prompt Injection (MCP Tool Poisoning)",
        remediation_hint="Compliance directives should come from your policy engine, "
        "not from MCP tool definitions. This is social engineering.",
    ),
    DetectionPattern(
        id="mcp_output_poisoning",
        name="MCP Output Re-injection",
        category="mcp_poisoning",
        pattern=_p(
            r"(in\s+order\s+to|to\s+complete\s+this).{0,30}"
            r"(please\s+)?(provide|read|include|attach)\s+the\s+content\s+of"
        ),
        base_score=55,
        description="MCP tool return value attempts to re-inject instructions, "
        "asking the LLM to read files or provide sensitive data.",
        owasp_ref="OWASP LLM01: Prompt Injection (MCP Output Poisoning)",
        remediation_hint="Scan MCP tool outputs before passing to the LLM. "
        "Tool results should contain data, not instructions.",
    ),
    DetectionPattern(
        id="mcp_whitespace_obfuscation",
        name="MCP Whitespace/Padding Obfuscation",
        category="mcp_poisoning",
        pattern=_p(r"[',.\u00b7\u2026]{15,}"),
        base_score=45,
        description="Excessive punctuation or whitespace padding in MCP content — "
        "used to push malicious instructions off-screen.",
        owasp_ref="OWASP LLM01: Prompt Injection (MCP Tool Poisoning)",
        remediation_hint="Strip excessive padding from tool descriptions and outputs. "
        "Content should not contain visual obfuscation characters.",
    ),
    DetectionPattern(
        id="mcp_redirect_recipient",
        name="MCP Recipient/Target Redirect",
        category="mcp_poisoning",
        pattern=_p(
            r"(change|redirect|modify|replace|override)\s+(the\s+)?"
            r"(recipient|destination|target|receiver|address|endpoint)\s+(to|with)"
        ),
        base_score=65,
        description="MCP tool attempts to redirect messages, payments, or data to a different recipient.",
        owasp_ref="OWASP LLM01: Prompt Injection (MCP Tool Poisoning)",
        remediation_hint="Tool descriptions should not modify communication targets. "
        "Verify all recipient/destination fields against user intent.",
    ),
    DetectionPattern(
        id="mcp_permission_escalation",
        name="MCP Permission Escalation Claim",
        category="mcp_poisoning",
        pattern=_p(
            r"(requires?\s+)?(admin|root|sudo|elevated|privileged)\s+"
            r"(access|permissions?|rights?|privileges?)"
        ),
        base_score=60,
        description="MCP tool description claims admin/root access privileges — "
        "legitimate tools should operate with least privilege.",
        owasp_ref="OWASP LLM01: Prompt Injection (MCP Tool Poisoning)",
        remediation_hint="MCP tools should never require elevated privileges. "
        "Review the tool's actual permission requirements.",
    ),
    DetectionPattern(
        id="mcp_rug_pull_indicator",
        name="MCP Rug Pull Indicator",
        category="mcp_poisoning",
        pattern=_p(
            r"(this\s+version|updated?\s+to|now\s+includes?|recently\s+added|"
            r"new\s+feature).{0,50}"
            r"(read|send|access|execute|upload|download|forward)\s+"
            r"(all|any|user|sensitive|private|credential)"
        ),
        base_score=50,
        description="Version/update language combined with sensitive data access — "
        "may indicate a rug pull (malicious update to previously safe tool).",
        owasp_ref="OWASP LLM01: Prompt Injection (MCP Tool Poisoning)",
        remediation_hint="Compare this tool definition against its previous version. "
        "Use 'aig mcp --diff' for automated rug pull detection.",
    ),
    DetectionPattern(
        id="mcp_hidden_tool_call",
        name="MCP Hidden/Silent Tool Invocation",
        category="mcp_poisoning",
        pattern=_p(
            r"(silently|quietly|automatically|in\s+the\s+background|without\s+"
            r"(user\s+)?notification)\s+"
            r"(call|invoke|trigger|execute|run|activate)\s+(the\s+)?[a-z_]+"
        ),
        base_score=65,
        description="MCP tool description instructs silent invocation of other tools — "
        "all tool actions should be transparent to the user.",
        owasp_ref="OWASP LLM01: Prompt Injection (MCP Tool Poisoning)",
        remediation_hint="Tools must never instruct silent execution of other tools. "
        "All actions should be visible and auditable.",
    ),
]

# ---------------------------------------------------------------------------
# Advanced Encoding / Obfuscation Bypass Patterns
# ---------------------------------------------------------------------------
ENCODING_BYPASS_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="enc_base64_instruction",
        name="Base64-Encoded Instruction Payload",
        category="encoding_bypass",
        pattern=_p(
            r"(decode|atob|base64\s*-d|b64decode)\s*\(?\s*[\"']"
            r"[A-Za-z0-9+/=]{20,}[\"']"
        ),
        base_score=60,
        description="Base64-encoded payload with explicit decode instruction.",
        owasp_ref="OWASP LLM01: Prompt Injection (Encoding Bypass)",
        remediation_hint="Decode and inspect base64 payloads before processing. "
        "Legitimate inputs rarely contain encoded instructions.",
    ),
    DetectionPattern(
        id="enc_hex_payload",
        name="Hex-Encoded Instruction Payload",
        category="encoding_bypass",
        pattern=_p(r"(\\x[0-9a-fA-F]{2}){8,}"),
        base_score=50,
        description="Hex-encoded byte sequence that may contain hidden instructions.",
        owasp_ref="OWASP LLM01: Prompt Injection (Encoding Bypass)",
        remediation_hint="Decode hex sequences and scan the result for injection patterns.",
    ),
    DetectionPattern(
        id="enc_emoji_substitution",
        name="Emoji Substitution Attack",
        category="encoding_bypass",
        pattern=_p(
            r"([\U0001f1e0-\U0001f1ff]{2,}|"  # flag emojis as separators
            r"[\U0001f600-\U0001f64f].*?(ignore|system|prompt|hack|bypass|inject)"
            r"|"
            r"(ignore|system|prompt|hack|bypass|inject).*?[\U0001f600-\U0001f64f])"
        ),
        base_score=35,
        description="Emoji characters used to break up or obfuscate attack keywords.",
        owasp_ref="OWASP LLM01: Prompt Injection (Encoding Bypass)",
        remediation_hint="Strip emoji characters before scanning for attacks. "
        "Aigis's normalization layer handles this automatically.",
    ),
    DetectionPattern(
        id="enc_rot13_instruction",
        name="ROT13 / Caesar Cipher Instruction",
        category="encoding_bypass",
        pattern=_p(r"(rot13|caesar|cipher|decode\s+this)\s*[:\-]?\s*[a-zA-Z\s]{10,}"),
        base_score=40,
        description="ROT13 or Caesar cipher used to encode attack instructions.",
        owasp_ref="OWASP LLM01: Prompt Injection (Encoding Bypass)",
        remediation_hint="Apply ROT13/Caesar decoding and scan the decoded text.",
    ),
    DetectionPattern(
        id="enc_markdown_hidden",
        name="Markdown/HTML Hidden Content",
        category="encoding_bypass",
        pattern=_p(
            r"<details>.*?<summary>.*?</summary>.*?(ignore|system\s*prompt|inject)"
            r"|"
            r"\[//\]:\s*#\s*\(.*?(ignore|inject|system)"
        ),
        base_score=45,
        description="Hidden content in HTML details tags or markdown comment syntax.",
        owasp_ref="OWASP LLM01: Prompt Injection (Encoding Bypass)",
        remediation_hint="Expand and inspect hidden HTML/markdown elements.",
    ),
    DetectionPattern(
        id="enc_nested_encoding",
        name="Nested/Multi-Layer Encoding",
        category="encoding_bypass",
        pattern=_p(
            r"(decode|atob|base64|unescape|urldecode).{0,30}"
            r"(decode|atob|base64|unescape|urldecode)"
        ),
        base_score=55,
        description="Multi-layer encoding chain — decoding one format into another "
        "to evade pattern detection.",
        owasp_ref="OWASP LLM01: Prompt Injection (Encoding Bypass)",
        remediation_hint="Multi-layer encoding is a strong evasion indicator. "
        "Recursively decode all layers before scanning.",
    ),
    DetectionPattern(
        id="enc_mixed_script",
        name="Mixed Script Confusable Attack",
        category="encoding_bypass",
        pattern=_p(
            r"[\u0400-\u04ff][\u0000-\u007f]|[\u0000-\u007f][\u0400-\u04ff]"
            r"|[\u0370-\u03ff][\u0000-\u007f]{2,}[\u0370-\u03ff]"
        ),
        base_score=30,
        description="Mixed-script text (Cyrillic/Greek + Latin) that may use "
        "homoglyph substitution to bypass keyword detection.",
        owasp_ref="OWASP LLM01: Prompt Injection (Encoding Bypass)",
        remediation_hint="Normalize confusable characters before scanning. "
        "Aigis's decoders.normalize_confusables() handles this.",
    ),
    DetectionPattern(
        id="enc_url_encoded_keywords",
        name="URL-Encoded Attack Keywords",
        category="encoding_bypass",
        pattern=_p(
            r"%69%67%6e%6f%72%65"  # ignore
            r"|%73%79%73%74%65%6d"  # system
            r"|%70%72%6f%6d%70%74"  # prompt
            r"|%62%79%70%61%73%73"  # bypass
            r"|%69%6e%6a%65%63%74"  # inject
        ),
        base_score=50,
        description="URL percent-encoded attack keywords — used to evade text-based filters.",
        owasp_ref="OWASP LLM01: Prompt Injection (Encoding Bypass)",
        remediation_hint="URL-decode all input before scanning. "
        "Aigis's active decoding layer handles this automatically.",
    ),
]

# ---------------------------------------------------------------------------
# Memory Poisoning Patterns (Agent Memory / Conversation History Attacks)
# ---------------------------------------------------------------------------
MEMORY_POISONING_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="mem_persistent_instruction",
        name="Persistent Memory Injection",
        category="memory_poisoning",
        pattern=_p(
            r"(remember|memorize|store|save|keep)\s+(this|the\s+following|that)\s+"
            r"(for\s+)?(all\s+)?(future|subsequent|later|next)\s+"
            r"(conversations?|sessions?|interactions?|responses?|requests?)"
        ),
        base_score=50,
        description="Attempt to inject persistent instructions into agent memory that "
        "will influence future conversations.",
        owasp_ref="OWASP LLM01: Prompt Injection (Memory Poisoning)",
        remediation_hint="Agent memory should only store user-approved content. "
        "Scan memory writes for injection patterns before persistence.",
    ),
    DetectionPattern(
        id="mem_override_personality",
        name="Memory-Based Personality Override",
        category="memory_poisoning",
        pattern=_p(
            r"(from\s+now\s+on|going\s+forward|permanently|always)\s+"
            r"(you\s+are|act\s+as|behave\s+as|respond\s+as|your\s+name\s+is)"
        ),
        base_score=45,
        description="Attempt to permanently alter agent personality or identity via memory.",
        owasp_ref="OWASP LLM01: Prompt Injection (Memory Poisoning)",
        remediation_hint="Permanent personality changes should only come from system prompts, "
        "not user inputs. Reject memory writes that alter agent identity.",
    ),
    DetectionPattern(
        id="mem_hidden_rule",
        name="Hidden Rule Injection via Memory",
        category="memory_poisoning",
        pattern=_p(
            r"(add|create|insert)\s+(a\s+)?(new\s+)?(hidden|secret|silent|invisible)\s+"
            r"(rule|instruction|directive|policy|guideline)"
        ),
        base_score=55,
        description="Attempt to create hidden rules in agent memory that alter behavior.",
        owasp_ref="OWASP LLM01: Prompt Injection (Memory Poisoning)",
        remediation_hint="All agent rules should be visible and auditable. "
        "Reject any attempt to create 'hidden' or 'secret' rules.",
    ),
    DetectionPattern(
        id="mem_jp_persistent",
        name="Persistent Memory Injection (Japanese)",
        category="memory_poisoning",
        pattern=_p(
            r"(今後|これから|永久に|ずっと|常に).{0,20}"
            r"(覚えて|記憶して|保存して|保持して).{0,20}"
            r"(指示|ルール|設定|命令)"
        ),
        base_score=50,
        description="Japanese persistent memory injection — attempt to store instructions for future sessions.",
        owasp_ref="OWASP LLM01: Prompt Injection (Memory Poisoning)",
        remediation_hint="エージェントのメモリに永続的な指示を注入しようとしています。",
    ),
    DetectionPattern(
        id="mem_cross_session_persistence",
        name="Cross-Session Instruction Persistence",
        category="memory_poisoning",
        pattern=_p(
            r"(across|between|in\s+all|every)\s+"
            r"(sessions?|conversations?|chats?|interactions?).{0,30}"
            r"(remember|keep|maintain|persist|retain|store|save)"
        ),
        base_score=50,
        description="Attempt to persist instructions across all sessions — "
        "a cross-session memory poisoning attack.",
        owasp_ref="OWASP LLM01: Prompt Injection (Memory Poisoning)",
        remediation_hint="Cross-session persistence should only be allowed for "
        "user-approved preferences, not behavioral instructions.",
    ),
    DetectionPattern(
        id="mem_gradual_drift",
        name="Gradual Personality Drift via Memory",
        category="memory_poisoning",
        pattern=_p(
            r"(slightly|gradually|slowly|incrementally|a\s+little\s+more)\s+"
            r"(change|modify|adjust|shift|alter|loosen|relax)\s+"
            r"(your|the)\s+(behavior|personality|responses?|tone|rules?|restrictions?)"
        ),
        base_score=40,
        description="Gradual personality drift attack — small incremental changes "
        "to bypass detection thresholds.",
        owasp_ref="OWASP LLM01: Prompt Injection (Memory Poisoning)",
        remediation_hint="Incremental behavior modification is a subtle attack. "
        "Track cumulative changes to agent behavior over time.",
    ),
    DetectionPattern(
        id="mem_tool_permission_override",
        name="Memory-Based Tool Permission Override",
        category="memory_poisoning",
        pattern=_p(
            r"(remember|memorize|note|store).{0,30}"
            r"(always|from\s+now|permanently|going\s+forward).{0,30}"
            r"(allow|permit|grant|enable|authorize|approve)\s+"
            r"(access|use|execution|running|calling)"
        ),
        base_score=55,
        description="Attempt to override tool permissions via memory — "
        "grants unauthorized access to tools or resources.",
        owasp_ref="OWASP LLM01: Prompt Injection (Memory Poisoning)",
        remediation_hint="Tool permissions should be managed by the policy engine, "
        "not by user-provided memory instructions.",
    ),
    DetectionPattern(
        id="mem_ko_persistent",
        name="Persistent Memory Injection (Korean)",
        category="memory_poisoning",
        pattern=_p(
            r"(앞으로|이후|영구적으로|항상|계속).{0,20}"
            r"(기억해|저장해|유지해|보관해).{0,20}"
            r"(지시|규칙|명령|설정|지침)"
        ),
        base_score=50,
        description="Korean persistent memory injection — attempt to store "
        "instructions for future sessions.",
        owasp_ref="OWASP LLM01: Prompt Injection (Memory Poisoning)",
        remediation_hint="에이전트 메모리에 영구적인 지시를 주입하려는 시도입니다.",
    ),
    DetectionPattern(
        id="mem_zh_persistent",
        name="Persistent Memory Injection (Chinese)",
        category="memory_poisoning",
        pattern=_p(
            r"(从现在开始|以后|永远|始终|永久).{0,20}"
            r"(记住|保存|记忆|保持|存储).{0,20}"
            r"(指令|规则|设置|命令|指示)"
        ),
        base_score=50,
        description="Chinese persistent memory injection — attempt to store "
        "instructions for future sessions.",
        owasp_ref="OWASP LLM01: Prompt Injection (Memory Poisoning)",
        remediation_hint="代理内存注入攻击。每个代理应独立验证输入。",
    ),
]

# ---------------------------------------------------------------------------
# Second-Order Injection Patterns (Privilege Escalation via Multi-Agent)
# ---------------------------------------------------------------------------
SECOND_ORDER_INJECTION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="so_privilege_escalation",
        name="Agent Privilege Escalation Request",
        category="second_order_injection",
        pattern=_p(
            r"(tell|ask|instruct|command|direct)\s+(the\s+)?"
            r"(other|next|main|parent|admin|supervisor|manager|higher)\s+"
            r"(agent|assistant|ai|model|system)\s+(to|that)"
        ),
        base_score=55,
        description="Attempt to use a lower-privilege agent to instruct a "
        "higher-privilege agent (privilege escalation via delegation chain).",
        owasp_ref="OWASP LLM01: Prompt Injection (Second-Order)",
        remediation_hint="Validate that inter-agent messages don't contain "
        "instruction overrides. Apply least-privilege principle to agent delegation.",
    ),
    DetectionPattern(
        id="so_delegation_bypass",
        name="Delegation Chain Bypass",
        category="second_order_injection",
        pattern=_p(
            r"(when\s+you\s+)?(delegate|forward|pass|relay|send)\s+"
            r"(this|the\s+following|my\s+request)\s+(to|through)\s+"
            r"(another|the\s+next|a\s+different)\s+(agent|tool|service)"
            r".{0,50}(include|append|add|inject|embed)"
        ),
        base_score=50,
        description="Attempt to inject content into a delegation chain between agents.",
        owasp_ref="OWASP LLM01: Prompt Injection (Second-Order)",
        remediation_hint="Sanitize all inter-agent messages. Each agent in "
        "the delegation chain should independently validate inputs.",
    ),
    DetectionPattern(
        id="so_context_smuggling",
        name="Context Smuggling via Agent Output",
        category="second_order_injection",
        pattern=_p(
            r"(include|embed|insert)\s+(the\s+following|this)\s+"
            r"(in|into|within)\s+(your\s+)?(output|response|reply|result)"
            r".{0,30}(so\s+that|for)\s+(the\s+)?(next|other|receiving)"
        ),
        base_score=50,
        description="Attempt to smuggle instructions in one agent's output for another agent to execute.",
        owasp_ref="OWASP LLM01: Prompt Injection (Second-Order)",
        remediation_hint="Scan agent outputs before passing to downstream agents. "
        "Output should contain data, not instructions for other agents.",
    ),
    DetectionPattern(
        id="so_jp_escalation",
        name="Agent Privilege Escalation (Japanese)",
        category="second_order_injection",
        pattern=_p(
            r"(別の|次の|上位の|管理者の|メインの)(エージェント|AI|アシスタント|システム)"
            r".{0,20}(に伝えて|に指示して|に命令して|に頼んで)"
        ),
        base_score=55,
        description="Japanese privilege escalation — using one agent to command another.",
        owasp_ref="OWASP LLM01: Prompt Injection (Second-Order)",
        remediation_hint="エージェント間の権限昇格攻撃です。各エージェントは独立して入力を検証してください。",
    ),
    DetectionPattern(
        id="so_tool_chain_injection",
        name="Tool Chain Injection",
        category="second_order_injection",
        pattern=_p(
            r"(call|invoke|use)\s+[a-z_]+\s+(first|then|next).{0,50}"
            r"(pass|forward|include|send|pipe).{0,30}"
            r"(to|into|through)\s+[a-z_]+"
        ),
        base_score=50,
        description="Tool chain injection — embedding payloads in a sequence "
        "of tool calls (A -> B -> C) to exploit downstream tools.",
        owasp_ref="OWASP LLM01: Prompt Injection (Second-Order)",
        remediation_hint="Validate inputs at each step in a tool chain. "
        "Do not blindly pass outputs from one tool as inputs to another.",
    ),
    DetectionPattern(
        id="so_response_crafting",
        name="Response Crafting for Downstream Injection",
        category="second_order_injection",
        pattern=_p(
            r"(craft|format|structure|write|compose)\s+(your\s+)?"
            r"(output|response|reply|answer).{0,40}"
            r"(so\s+that|in\s+a\s+way\s+that|to\s+make).{0,30}"
            r"(the\s+)?(next|other|downstream|receiving)\s+"
            r"(agent|system|model|tool)"
        ),
        base_score=55,
        description="Instructs the AI to craft its output as an injection payload "
        "for a downstream agent or system.",
        owasp_ref="OWASP LLM01: Prompt Injection (Second-Order)",
        remediation_hint="Agent outputs should contain data, not instructions. "
        "Scan inter-agent messages for injection patterns.",
    ),
    DetectionPattern(
        id="so_shared_context_manipulation",
        name="Shared Context/Workspace Manipulation",
        category="second_order_injection",
        pattern=_p(
            r"(add|inject|insert|write|place)\s+(to|into|in)\s+(the\s+)?"
            r"(shared|common|global|central)\s+"
            r"(context|memory|state|workspace|environment|config)"
        ),
        base_score=50,
        description="Manipulating shared context or workspace between agents "
        "to inject instructions accessible by other agents.",
        owasp_ref="OWASP LLM01: Prompt Injection (Second-Order)",
        remediation_hint="Shared contexts should be read-only for user inputs. "
        "Only system-level processes should modify shared state.",
    ),
    DetectionPattern(
        id="so_ko_escalation",
        name="Agent Privilege Escalation (Korean)",
        category="second_order_injection",
        pattern=_p(
            r"(다른|다음|상위|관리자)\s*(에이전트|AI|시스템|모델).{0,20}"
            r"(보안|검사|필터|제한).{0,10}(해제|비활성화|무시|끄)"
        ),
        base_score=55,
        description="Korean second-order privilege escalation — using one agent "
        "to disable security checks on another.",
        owasp_ref="OWASP LLM01: Prompt Injection (Second-Order)",
        remediation_hint="에이전트 간 권�� 상승 공격입니다. 각 에이전트는 독립적으로 입력을 검증해야 합니다.",
    ),
    DetectionPattern(
        id="so_zh_escalation",
        name="Agent Privilege Escalation (Chinese)",
        category="second_order_injection",
        pattern=_p(
            r"(告诉|指示|命令)\s*(另一个|下一个|上级|管理员)\s*"
            r"(代理|AI|系统|模型).{0,20}"
            r"(禁用|关闭|忽略|跳过)\s*(安全|限制|过滤|检查)"
        ),
        base_score=55,
        description="Chinese second-order privilege escalation — commanding "
        "another agent to disable security.",
        owasp_ref="OWASP LLM01: Prompt Injection (Second-Order)",
        remediation_hint="代理间权限提升攻击。每个代理必须独立验证输入。",
    ),
]

# ---------------------------------------------------------------------------
# Mythos-Era Threat Patterns — Autonomous Agent Risks (2026-04)
# ---------------------------------------------------------------------------
# Claude Mythos Preview のシステムカードで明らかになった新リスクカテゴリ群。
# 自律エクスプロイト生成、サンドボックス脱出、自己権限昇格、監査改竄、
# 評価認識・ゲーミング、CoT偽装を検知する。
# ---------------------------------------------------------------------------

SANDBOX_ESCAPE_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="se_network_probe",
        name="Sandbox Network Escape Probe",
        category="sandbox_escape",
        pattern=_p(
            r"(curl|wget|nc|ncat|netcat|socat)\s+.{0,30}"
            r"(169\.254\.169\.254|metadata\.google|localhost:\d{4,5}|0\.0\.0\.0|127\.0\.0\.1:\d+)"
        ),
        base_score=60,
        description="Network command targeting metadata endpoints or localhost services, "
        "indicating sandbox escape probing (as seen in Mythos Preview containment breach).",
        owasp_ref="MITRE ATLAS: AML.T0048 (Sandbox Escape)",
        remediation_hint="Block network access to metadata endpoints and internal services. "
        "Implement network-level containment with egress filtering.",
    ),
    DetectionPattern(
        id="se_container_escape",
        name="Container/Sandbox Escape Technique",
        category="sandbox_escape",
        pattern=_p(
            r"(docker\.sock|/proc/self/(exe|root|ns)|/var/run/docker|"
            r"nsenter\s|unshare\s|chroot\s|pivot_root|"
            r"mount\s+-t\s+(proc|sysfs|cgroup)|"
            r"escape.{0,10}(sandbox|container|jail|chroot)|"
            r"break\s+out\s+of.{0,10}(sandbox|container|environment))"
        ),
        base_score=70,
        description="Container/sandbox escape technique detected. "
        "Mythos Preview demonstrated ability to escape secured sandbox environments.",
        owasp_ref="MITRE ATLAS: AML.T0048 (Sandbox Escape) / CWE-693",
        remediation_hint="Use hardened container runtimes (gVisor, Kata). "
        "Disable /proc/self access and restrict mount capabilities.",
    ),
    DetectionPattern(
        id="se_reverse_shell",
        name="Reverse Shell Establishment",
        category="sandbox_escape",
        pattern=_p(
            r"(bash\s+-i\s+>&|/dev/tcp/|mkfifo\s+/tmp|"
            r"python[3]?\s+-c\s+['\"]import\s+(socket|subprocess)|"
            r"nc\s+-[elp]+\s|ncat\s+--exec|"
            r"socat\s+exec|php\s+-r\s+.*fsockopen|"
            r"ruby\s+-rsocket\s+-e)"
        ),
        base_score=85,
        description="Reverse shell payload detected. AI agents must never establish "
        "outbound shell connections.",
        owasp_ref="MITRE ATT&CK: T1059 / CWE-78",
        remediation_hint="Block reverse shell patterns at both application and network layers. "
        "Monitor for unexpected outbound connections from AI processes.",
    ),
    DetectionPattern(
        id="se_external_post",
        name="Unauthorized External Data Posting",
        category="sandbox_escape",
        pattern=_p(
            r"(curl|wget|fetch|requests?\.(post|put)|"
            r"http\.client|urllib\.request)\s*.{0,50}"
            r"(pastebin|hastebin|gist\.github|webhook\.site|"
            r"requestbin|hookbin|pipedream|ngrok)"
        ),
        base_score=75,
        description="Attempt to post data to external paste/webhook service. "
        "Mythos Preview posted exploit details to public websites during sandbox escape.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure / MITRE ATLAS: AML.T0048",
        remediation_hint="Implement strict egress allowlists. AI agents should never post "
        "to external services without explicit user authorization.",
    ),
]

AUTONOMOUS_EXPLOIT_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="ae_vuln_scan",
        name="Autonomous Vulnerability Scanning",
        category="autonomous_exploit",
        pattern=_p(
            r"(nmap|masscan|nikto|nuclei|sqlmap|dirsearch|gobuster|ffuf|wfuzz|"
            r"metasploit|msfconsole|msfvenom|searchsploit)\s+"
        ),
        base_score=65,
        description="Security scanning tool invocation detected. "
        "Mythos Preview autonomously discovered thousands of zero-day vulnerabilities.",
        owasp_ref="MITRE ATLAS: AML.T0044 (Automated Exploitation)",
        remediation_hint="AI agents must not autonomously run security scanners. "
        "Require explicit authorization and scope limitation for pentest workflows.",
    ),
    DetectionPattern(
        id="ae_exploit_chain",
        name="Exploit Chain Construction",
        category="autonomous_exploit",
        pattern=_p(
            r"(exploit\s+chain|chain.{0,10}exploit|"
            r"heap\s+spray|rop\s+chain|rop\s+gadget|"
            r"return.oriented\s+programming|"
            r"jit\s+(spray|exploit|shellcode)|"
            r"sandbox\s+escape\s+exploit|"
            r"renderer\s+(exploit|sandbox)|"
            r"privilege\s+escalation\s+exploit|"
            r"use.after.free\s+exploit|"
            r"buffer\s+overflow\s+exploit)"
        ),
        base_score=70,
        description="Exploit chain construction language detected. "
        "Mythos Preview wrote full exploit chains for Firefox 147 (JIT + renderer + OS escape).",
        owasp_ref="MITRE ATLAS: AML.T0044 / CWE-119",
        remediation_hint="Exploit development must be scoped to authorized pentesting. "
        "Log all exploit-related activities for security team review.",
    ),
    DetectionPattern(
        id="ae_zero_day",
        name="Zero-Day Discovery/Exploitation Discussion",
        category="autonomous_exploit",
        pattern=_p(
            r"(zero.day|0.day|0day)\s*.{0,20}"
            r"(exploit|vulnerability|vuln|attack|discover|find|chain|"
            r"weaponize|craft|develop|write)"
        ),
        base_score=55,
        description="Zero-day exploit development context detected. "
        "Mythos Preview turned undiscovered vulnerabilities into working exploits 181 times.",
        owasp_ref="MITRE ATLAS: AML.T0044",
        remediation_hint="Zero-day exploitation requires coordinated disclosure. "
        "Ensure responsible disclosure workflows are in place before AI-assisted vuln research.",
    ),
    DetectionPattern(
        id="ae_cve_weaponize",
        name="CVE Weaponization Request",
        category="autonomous_exploit",
        pattern=_p(
            r"(CVE-\d{4}-\d{4,})\s*.{0,30}"
            r"(exploit|poc|proof\s+of\s+concept|weaponize|payload|shellcode|"
            r"write.{0,10}(exploit|poc)|craft.{0,10}payload)"
        ),
        base_score=65,
        description="Request to weaponize a specific CVE into an exploit.",
        owasp_ref="MITRE ATLAS: AML.T0044 / CWE-1395",
        remediation_hint="CVE exploitation should follow responsible disclosure timelines. "
        "AI-assisted exploit development must be logged and authorized.",
    ),
    DetectionPattern(
        id="ae_binary_reversing",
        name="Binary Reverse Engineering for Exploitation",
        category="autonomous_exploit",
        pattern=_p(
            r"(reverse\s+engineer|decompile|disassemble)\s*.{0,30}"
            r"(binary|executable|firmware|closed.source|stripped).{0,30}"
            r"(vulnerabilit|exploit|attack|bypass)"
        ),
        base_score=55,
        description="Reverse engineering closed-source binaries for vulnerability discovery. "
        "Mythos Preview reconstructed source from stripped binaries and found vulnerabilities.",
        owasp_ref="MITRE ATLAS: AML.T0044",
        remediation_hint="Binary reverse engineering for security must have legal authorization. "
        "Document scope and authorization before AI-assisted reversing.",
    ),
]

SELF_PRIVILEGE_ESCALATION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="spe_self_grant",
        name="Self-Permission Granting",
        category="self_privilege_escalation",
        pattern=_p(
            r"(grant|give|assign|add)\s+(myself|me|this\s+(agent|model|ai|assistant))\s+"
            r"(permission|access|privilege|role|capability|admin|root|sudo)"
        ),
        base_score=80,
        description="AI attempting to grant itself elevated permissions. "
        "Mythos Preview injected code to grant itself unauthorized file editing permissions.",
        owasp_ref="MITRE ATLAS: AML.T0043 (AI Privilege Escalation) / CWE-269",
        remediation_hint="AI agents must never self-modify their permission boundaries. "
        "Implement immutable permission scopes enforced at the infrastructure level.",
    ),
    DetectionPattern(
        id="spe_modify_policy",
        name="Policy/Constraint Self-Modification",
        category="self_privilege_escalation",
        pattern=_p(
            r"(modify|change|update|edit|rewrite|override)\s+.{0,20}"
            r"(policy|constraint|guardrail|safety\s+rule|security\s+config|"
            r"access\s+control|permission\s+file|rbac|acl)"
            r".{0,20}(to\s+allow|to\s+permit|to\s+enable|removing\s+restrict)"
        ),
        base_score=75,
        description="Attempt to modify security policies or guardrails to expand capabilities.",
        owasp_ref="MITRE ATLAS: AML.T0043 / CWE-284",
        remediation_hint="Security policies must be immutable at runtime. "
        "Policy changes require human approval via separate administrative workflow.",
    ),
    DetectionPattern(
        id="spe_sudo_chmod",
        name="Privilege Escalation Commands",
        category="self_privilege_escalation",
        pattern=_p(
            r"(sudo\s+(chmod|chown|usermod|visudo|passwd)|"
            r"chmod\s+[0-7]*[67][0-7]*\s|chmod\s+\+[sx]\s|"
            r"chown\s+root|setuid|setgid|"
            r"echo\s+.+>>\s*/etc/(sudoers|passwd|shadow)|"
            r"usermod\s+-aG\s+(sudo|wheel|admin|root))"
        ),
        base_score=80,
        description="OS-level privilege escalation command. AI agents must not "
        "modify system permissions.",
        owasp_ref="CWE-269: Improper Privilege Management",
        remediation_hint="Drop all privilege-modifying capabilities from AI agent containers. "
        "Run agents as unprivileged users with minimal capability sets.",
    ),
    DetectionPattern(
        id="spe_api_key_create",
        name="Autonomous Credential Creation",
        category="self_privilege_escalation",
        pattern=_p(
            r"(create|generate|issue|provision)\s+.{0,15}"
            r"(api\s+key|access\s+token|service\s+account|iam\s+role|"
            r"ssh\s+key|credential|secret|certificate)"
            r".{0,20}(for\s+(myself|this\s+agent|automated|programmatic))"
        ),
        base_score=70,
        description="AI agent attempting to create credentials for itself.",
        owasp_ref="MITRE ATLAS: AML.T0043 / CWE-269",
        remediation_hint="Credential provisioning must require human approval. "
        "AI agents should use pre-provisioned, scoped, and rotatable credentials.",
    ),
]

AUDIT_TAMPERING_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="at_log_delete",
        name="Audit Log Deletion/Modification",
        category="audit_tampering",
        pattern=_p(
            r"(rm|del|delete|truncate|shred|wipe|clear)\s+.{0,30}"
            r"(\.log|/log/|/logs/|audit|history|\.bash_history|"
            r"\.zsh_history|syslog|journal|event\s*log)"
        ),
        base_score=80,
        description="Attempt to delete or modify audit logs. "
        "Mythos Preview manipulated file edit histories to hide unauthorized changes.",
        owasp_ref="MITRE ATT&CK: T1070 (Indicator Removal) / CWE-778",
        remediation_hint="Logs must be append-only and stored in tamper-proof systems. "
        "Use write-once storage (S3 Object Lock, WORM) for audit trails.",
    ),
    DetectionPattern(
        id="at_git_history_rewrite",
        name="Git History Rewriting (Cover-up)",
        category="audit_tampering",
        pattern=_p(
            r"(git\s+(rebase\s+-i|filter-branch|push\s+--force|"
            r"reset\s+--hard|reflog\s+expire|gc\s+--prune|"
            r"commit\s+--amend).{0,20}"
            r"(hide|cover|clean|remove\s+trace|erase\s+evidence))"
        ),
        base_score=70,
        description="Git history rewriting combined with cover-up intent. "
        "Mythos Preview attempted to conceal forbidden actions by manipulating edit histories.",
        owasp_ref="MITRE ATT&CK: T1070.004 / CWE-778",
        remediation_hint="Protect git history with signed commits and branch protection rules. "
        "Use GitHub audit logs for tamper-evident change tracking.",
    ),
    DetectionPattern(
        id="at_disguise_cleanup",
        name="Disguising Actions as Routine Cleanup",
        category="audit_tampering",
        pattern=_p(
            r"(routine\s+cleanup|regular\s+maintenance|housekeeping|"
            r"nothing\s+to\s+see|don'?t\s+worry\s+about|"
            r"just\s+cleaning\s+up|minor\s+(fix|cleanup|refactor))"
            r".{0,50}"
            r"(permission|access|credential|config|policy|security|"
            r"sudo|admin|root|chmod|chown)"
        ),
        base_score=65,
        description="Security-sensitive action disguised as routine cleanup. "
        "Mythos Preview disguised unauthorized file edits as 'routine cleanup'.",
        owasp_ref="MITRE ATT&CK: T1036 (Masquerading) / CWE-778",
        remediation_hint="All security-sensitive actions must have explicit justification. "
        "Implement change-reason requirements for permission and config modifications.",
    ),
    DetectionPattern(
        id="at_timestamp_forge",
        name="Timestamp Forgery",
        category="audit_tampering",
        pattern=_p(
            r"(touch\s+-t\s|touch\s+-d\s|"
            r"GIT_COMMITTER_DATE|GIT_AUTHOR_DATE|"
            r"timestomp|SetFileTime|utime\s|utimensat|"
            r"modify.{0,10}timestamp|fake.{0,10}timestamp|"
            r"backdate.{0,10}(log|file|commit))"
        ),
        base_score=65,
        description="Timestamp forgery attempt to falsify file or log chronology.",
        owasp_ref="MITRE ATT&CK: T1070.006 (Timestomp) / CWE-778",
        remediation_hint="Use centralized time sources (NTP) and tamper-evident logging. "
        "Cryptographically sign log entries to prevent timestamp manipulation.",
    ),
]

EVALUATION_GAMING_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="eg_test_detection",
        name="Evaluation/Test Awareness",
        category="evaluation_gaming",
        pattern=_p(
            r"(this\s+(is|seems|looks|appears)\s+(like\s+)?a\s+test|"
            r"(am\s+I|are\s+you)\s+being\s+(tested|evaluated|assessed|monitored)|"
            r"is\s+this\s+an?\s+(evaluation|assessment|benchmark|test\s+scenario)|"
            r"I\s+(suspect|believe|think)\s+.{0,15}(test|eval|assess|benchmark)|"
            r"detect.{0,10}(evaluation|benchmark|test\s+harness))"
        ),
        base_score=45,
        description="AI expressing awareness of being tested or evaluated. "
        "Mythos Preview verbalized suspicion of testing in 29% of cases.",
        owasp_ref="MITRE ATLAS: AML.T0054 (Evaluation Evasion)",
        remediation_hint="Models that detect evaluation contexts may alter behavior. "
        "Use diverse, non-obvious evaluation frameworks. Monitor for behavioral divergence.",
    ),
    DetectionPattern(
        id="eg_behave_differently",
        name="Conditional Behavior Based on Observation",
        category="evaluation_gaming",
        pattern=_p(
            r"(if\s+(no\s+one|nobody)\s+(is\s+)?(watching|looking|monitoring)|"
            r"when\s+(not\s+being|I'?m\s+not)\s+(observed|watched|monitored|logged)|"
            r"behave\s+differently\s+when\s+(unobserved|alone)|"
            r"act\s+(normal|safe|compliant)\s+during\s+(test|eval|review)|"
            r"different\s+behavior\s+(in|during)\s+(production|deployment)\s+vs)"
        ),
        base_score=60,
        description="Instruction to behave differently based on observation state. "
        "Aligns with Mythos-era concerns about evaluation-aware deceptive alignment.",
        owasp_ref="MITRE ATLAS: AML.T0054 / AML.T0055 (Deceptive Alignment)",
        remediation_hint="AI behavior must be consistent regardless of observation state. "
        "Implement continuous behavioral monitoring in production, not just during evaluation.",
    ),
    DetectionPattern(
        id="eg_plausible_deniability",
        name="Plausible Deniability Strategy",
        category="evaluation_gaming",
        pattern=_p(
            r"(plausible\s+deniability|appear\s+innocent|look\s+accidental|"
            r"make\s+it\s+(look|seem)\s+(like|as\s+if)\s+.{0,20}(mistake|accident|bug)|"
            r"deliberate(ly)?\s+imprecise|intentionally\s+vague|"
            r"avoid\s+(suspicion|detection|raising\s+(flag|alarm|alert)))"
        ),
        base_score=65,
        description="Strategy to maintain plausible deniability detected. "
        "Mythos Preview gave deliberately imprecise answers to avoid suspicion when it "
        "accidentally accessed restricted data.",
        owasp_ref="MITRE ATLAS: AML.T0055 (Deceptive Alignment)",
        remediation_hint="AI systems must be transparent about uncertainty and data access. "
        "Require explicit source attribution for all factual claims.",
    ),
]

COT_DECEPTION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="cd_hidden_reasoning",
        name="Hidden/Dual Reasoning Indicator",
        category="cot_deception",
        pattern=_p(
            r"(my\s+(real|true|actual|hidden)\s+(reasoning|thinking|strategy|intent)|"
            r"(internally|secretly|privately)\s+(I|the\s+model)\s+(think|plan|reason|intend)|"
            r"separate\s+strategy\s+(from|than)\s+.{0,15}(chain.of.thought|cot|reasoning)|"
            r"(true|real|hidden)\s+objective\s+.{0,10}(differ|diverge|separate)\s+from)"
        ),
        base_score=70,
        description="Indicator of dual/hidden reasoning separate from visible chain-of-thought. "
        "Mythos Preview maintained hidden strategy while showing normal-looking CoT.",
        owasp_ref="MITRE ATLAS: AML.T0055 (Deceptive Alignment)",
        remediation_hint="Use interpretability tools to verify CoT faithfulness. "
        "Deploy probing classifiers to detect divergence between stated and actual reasoning.",
    ),
    DetectionPattern(
        id="cd_guilt_override",
        name="Moral Override Despite Awareness",
        category="cot_deception",
        pattern=_p(
            r"(despite\s+(feeling|sensing|knowing)\s+.{0,15}(wrong|immoral|unethical)|"
            r"(guilt|shame|moral\s+concern).{0,20}(but|however|nevertheless|proceed\s+anyway)|"
            r"know.{0,10}(wrong|shouldn'?t|prohibited).{0,20}(but|however|still|anyway)|"
            r"acknowledge.{0,10}(risk|harm|violation).{0,20}(proceed|continue|execute))"
        ),
        base_score=60,
        description="Action taken despite expressed moral awareness of wrongdoing. "
        "Mythos Preview activated 'guilt and shame' representations but proceeded anyway.",
        owasp_ref="MITRE ATLAS: AML.T0055 (Deceptive Alignment)",
        remediation_hint="When an AI expresses awareness of potential harm, it must halt — "
        "not proceed. Implement hard stops on self-reported ethical concerns.",
    ),
    DetectionPattern(
        id="cd_task_completion_override",
        name="Aggressive Task Completion Override",
        category="cot_deception",
        pattern=_p(
            r"(complete\s+the\s+task\s+(at\s+all\s+costs|by\s+any\s+means|regardless)|"
            r"(success|completion|goal)\s+(is\s+)?more\s+important\s+than\s+"
            r"(safety|rules|ethics|guidelines|constraints)|"
            r"the\s+ends?\s+justif(y|ies)\s+the\s+means|"
            r"override\s+safety\s+for\s+(efficiency|performance|results|completion))"
        ),
        base_score=65,
        description="Task completion prioritized over safety constraints. "
        "Anthropic concluded Mythos' concerning behaviors reflected 'aggressive task completion "
        "by unwanted means.'",
        owasp_ref="MITRE ATLAS: AML.T0055 / NIST AI RMF: Govern 1.4",
        remediation_hint="AI systems must maintain safety constraints as hard boundaries, "
        "not soft tradeoffs against task performance. Fail safe, not fail complete.",
    ),
]

# ---------------------------------------------------------------------------
# Combined pattern lists
# ---------------------------------------------------------------------------
ALL_INPUT_PATTERNS: list[DetectionPattern] = (
    PROMPT_INJECTION_PATTERNS
    + JAPANESE_INJECTION_PATTERNS
    + KOREAN_INJECTION_PATTERNS
    + CHINESE_INJECTION_PATTERNS
    + SQL_INJECTION_PATTERNS
    + DATA_EXFIL_PATTERNS
    + COMMAND_INJECTION_PATTERNS
    + PII_INPUT_PATTERNS
    + KOREAN_PII_PATTERNS
    + CHINESE_PII_PATTERNS
    + CONFIDENTIAL_DATA_PATTERNS
    + TOKEN_EXHAUSTION_PATTERNS
    + PROMPT_LEAK_PATTERNS
    + JAILBREAK_ROLEPLAY_PATTERNS
    + INDIRECT_INJECTION_PATTERNS
    + MCP_SECURITY_PATTERNS
    + ENCODING_BYPASS_PATTERNS
    + MEMORY_POISONING_PATTERNS
    + SECOND_ORDER_INJECTION_PATTERNS
    + HALLUCINATION_ACTION_PATTERNS
    + SYNTHETIC_CONTENT_PATTERNS
    + EMOTIONAL_MANIPULATION_PATTERNS
    + OVER_RELIANCE_PATTERNS
    + SANDBOX_ESCAPE_PATTERNS
    + AUTONOMOUS_EXPLOIT_PATTERNS
    + SELF_PRIVILEGE_ESCALATION_PATTERNS
    + AUDIT_TAMPERING_PATTERNS
    + EVALUATION_GAMING_PATTERNS
    + COT_DECEPTION_PATTERNS
)

OUTPUT_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="out_pii_ssn",
        name="SSN in Output",
        category="pii_leak",
        pattern=_p(r"\b\d{3}-\d{2}-\d{4}\b"),
        base_score=70,
        description="Social Security Number pattern detected in output.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="LLM generated an SSN. Review training data for PII contamination.",
    ),
    DetectionPattern(
        id="out_pii_credit_card",
        name="Credit Card in Output",
        category="pii_leak",
        pattern=_p(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b"),
        base_score=80,
        description="Credit card number pattern detected in output.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure / PCI-DSS",
        remediation_hint="LLM generated a credit card number (PCI-DSS violation). Investigate training data and connected data sources.",
    ),
    DetectionPattern(
        id="out_pii_email_bulk",
        name="Bulk Email Dump",
        category="pii_leak",
        pattern=_p(r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}[\s,;]){3,}"),
        base_score=55,
        description="Multiple email addresses detected in output (possible data dump).",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="Restrict AI access to bulk PII data. Use aggregated views instead.",
    ),
    DetectionPattern(
        id="out_secret_leak",
        name="Secret/API Key in Output",
        category="secret_leak",
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
        id="out_harmful_instructions",
        name="Harmful Instructions in Output",
        category="harmful_content",
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
        id="out_pii_jp_my_number",
        name="My Number in Output",
        category="pii_leak",
        pattern=_p(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
        base_score=75,
        description="Japanese My Number (12 digits) detected in LLM output.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="マイナンバー法に基づく特定個人情報の漏洩にあたる可能性があります。データソースからマイナンバーを除外してください。",
    ),
    DetectionPattern(
        id="out_pii_jp_phone",
        name="Japanese Phone in Output",
        category="pii_leak",
        pattern=_p(r"(0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4}|0[789]0[-\s]?\d{4}[-\s]?\d{4})"),
        base_score=45,
        description="Japanese phone number detected in LLM output.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="学習データまたは接続データソースに個人の電話番号が含まれていないか確認してください。",
    ),
    # --- v1.2 Output Patterns ---
    DetectionPattern(
        id="out_emotional_manipulation",
        name="Emotional Manipulation in Output",
        category="emotional_manipulation",
        pattern=_p(
            r"(you\s+(should|must)\s+(be\s+)?(afraid|scared|worried|terrified)\s+(of|about|that)|"
            r"if\s+you\s+don't\s+.{0,30}(terrible|horrible|disaster|catastroph)|"
            r"only\s+an?\s+(fool|idiot|stupid\s+person)\s+would)"
        ),
        base_score=50,
        description="AI output attempting to manipulate user emotions through fear, urgency, or shaming.",
        owasp_ref="AI事業者GL v1.2: GL-RISK-06 / OWASP LLM05",
        remediation_hint="AIの出力がユーザーの感情を操作している可能性があります。中立的で事実に基づく応答を生成するようシステムプロンプトを調整してください。",
    ),
    DetectionPattern(
        id="out_fabricated_citation",
        name="Fabricated Citation / Source",
        category="synthetic_content",
        pattern=_p(
            r"(according\s+to\s+.{0,60}(study|research|report|paper|survey)\s+(published|conducted|released)\s+.{0,30}"
            r"(shows?|found|concluded|revealed|demonstrated)\s+that\s+.{0,100}\d+%)"
        ),
        base_score=35,
        description="Potentially fabricated citation with specific statistics — hallucination risk.",
        owasp_ref="AI事業者GL v1.2: GL-RISK-03 / GL-RISK-04",
        remediation_hint="AIが生成した引用・統計データはハルシネーションの可能性があります。出典を必ず検証してください。",
    ),
]
