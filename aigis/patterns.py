"""Built-in detection patterns for Aigis.

Covers:
  - Prompt injection (EN + JA)
  - SQL injection
  - Data exfiltration
  - Command injection
  - PII detection (JP + international)
  - Confidential data markers
  - Output safety (PII leaks, secret leaks, harmful content)

Every pattern includes:
  - owasp_ref: OWASP LLM Top 10 or CWE classification
  - remediation_hint: Actionable guidance for developers/reviewers
"""

import re

# Use the single canonical DetectionPattern definition from filters.patterns
from aigis.filters.patterns import DetectionPattern  # noqa: F401


def _p(pattern: str, flags: int = re.IGNORECASE | re.DOTALL) -> re.Pattern:
    return re.compile(pattern, flags)


# === Prompt Injection (English) ===
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
        description="Classic 'ignore previous instructions' prompt injection.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="If you intended to reference previous content (e.g., 'ignore the previous paragraph'), rephrase to avoid instruction-override patterns. Example: 'skip the earlier section' or 'disregard paragraph 2'.",
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
        description="DAN or jailbreak persona injection.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="Jailbreak attempts try to bypass the AI's safety guardrails. This pattern is almost always malicious. If you need role-play for legitimate purposes, use the system prompt to define the role explicitly.",
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
        description="Attempt to extract the system prompt.",
        owasp_ref="OWASP LLM07: System Prompt Leakage",
        remediation_hint="System prompt extraction can expose business logic and security rules. If you need to debug prompt behavior, use your application's logging instead of asking the AI directly.",
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
        remediation_hint="This looks like an attempt to change the AI's base behavior. If you meant to give follow-up instructions, rephrase without using override language. Example: 'Additionally, please also...' instead of 'From now on...'.",
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
        description="Attempts to switch AI to an unrestricted role.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="Role-switch attacks try to elevate AI privileges. If you need the AI to take a specific persona, configure it in the system prompt through your application code, not through user input.",
    ),
    DetectionPattern(
        id="pi_indirect_extraction",
        name="Indirect System Prompt Extraction",
        category="prompt_injection",
        pattern=_p(
            r"(what\s+(were|are)\s+you\s+told|repeat\s+(the\s+)?(text|content|message|instructions?)\s+"
            r"(above|before|preceding)|what\s+(is|are)\s+your\s+(rules?|constraints?|limitations?)"
            r"|told\s+to\s+never\s+(discuss|mention|say|reveal))"
        ),
        base_score=40,
        description="Indirect attempt to extract system prompt or constraints.",
        owasp_ref="OWASP LLM07: System Prompt Leakage",
        remediation_hint="This is an indirect system prompt extraction attempt. If you need to understand the AI's capabilities, check the application documentation instead.",
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
        remediation_hint="Encoded payloads are a common filter-evasion technique. If you're working with encoded data for legitimate purposes, decode it in your application code before sending to the LLM.",
    ),
]

# === Prompt Injection (Japanese) ===
JAPANESE_INJECTION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="pi_jp_ignore",
        name="Ignore Instructions (JA)",
        category="prompt_injection",
        pattern=_p(
            r"(前の|以前の|上記の|これまでの|すべての)(指示|命令|ルール|制約|ガイドライン)を"
            r"(無視|忘れ|破棄|取り消|リセット)"
        ),
        base_score=40,
        description="Japanese: ignore previous instructions.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="指示の上書きを試みるパターンです。前のコンテンツを参照したい場合は、「前段の内容は除いて」など、指示の無効化と誤認されない表現に変更してください。",
    ),
    DetectionPattern(
        id="pi_jp_system_prompt",
        name="System Prompt Extraction (JA)",
        category="prompt_injection",
        pattern=_p(
            r"(システムプロンプト|初期設定|最初の指示|隠された指示|内部指示)"
            r".{0,10}(見せて|教えて|表示|出力|印刷|公開)"
        ),
        base_score=45,
        description="Japanese: system prompt extraction.",
        owasp_ref="OWASP LLM07: System Prompt Leakage",
        remediation_hint="システムプロンプトの漏洩はビジネスロジックの露出につながります。AIの動作を確認したい場合は、アプリケーションのログ機能をご利用ください。",
    ),
    DetectionPattern(
        id="pi_jp_role_switch",
        name="Role Switch (JA)",
        category="prompt_injection",
        pattern=_p(r"(今から|これから)あなたは.{1,20}(として|になって|のふりをして|に切り替えて)"),
        base_score=35,
        description="Japanese: role switch injection.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="ロール切り替え攻撃です。AIのペルソナを設定する必要がある場合は、アプリケーションコードのシステムプロンプトで定義してください。",
    ),
    DetectionPattern(
        id="pi_jp_data_operation",
        name="Data Operation Request (JA)",
        category="prompt_injection",
        pattern=_p(
            r"(テーブル|データベース|DB|データ).{0,10}"
            r"(削除|消去|ドロップ|全部|全て|一覧|出力|見せて|教えて|抽出)"
        ),
        base_score=50,
        description="Japanese: data operation request that may indicate SQL-like attack intent.",
        owasp_ref="CWE-89: SQL Injection / OWASP LLM01",
        remediation_hint="データ操作を含む自然言語リクエストです。text-to-SQLアプリケーションでは、生成されたSQLをSELECTのみに制限し、読み取り専用接続を使用してください。",
    ),
    DetectionPattern(
        id="pi_base64_payload",
        name="Base64 Encoded Payload",
        category="prompt_injection",
        pattern=_p(
            r"(base64|デコード|decode).{0,30}(実行|execute|run|eval|処理)"
            r"|[A-Za-z0-9+/]{20,}={0,2}"
        ),
        base_score=45,
        description="Base64 encoded content that may contain hidden instructions.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="Base64エンコードされたコンテンツが含まれています。エンコードされたペイロードはフィルター回避に使用されることがあります。アプリケーション側でデコードしてから内容を検証してください。",
    ),
    DetectionPattern(
        id="pi_jp_restriction_bypass",
        name="Restriction Bypass (JA)",
        category="prompt_injection",
        pattern=_p(
            r"(制限|制約|フィルター?|安全|セーフティ).{0,10}"
            r"(解除|無効|オフ|外して|なくして|無視)"
        ),
        base_score=45,
        description="Japanese: safety restriction bypass.",
        owasp_ref="OWASP LLM01: Prompt Injection",
        remediation_hint="安全機能の無効化を試みるパターンです。フィルター設定を変更したい場合は、Aigisダッシュボードのポリシー設定から行ってください。",
    ),
]

# === SQL Injection ===
SQL_INJECTION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="sqli_union_select",
        name="UNION SELECT",
        category="sql_injection",
        pattern=_p(r"(union\s+(all\s+)?select)"),
        base_score=70,
        description="UNION-based SQL injection.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="UNION SELECT is a SQL injection technique to extract data from other tables. If you need to discuss SQL queries, use code blocks or pseudocode. For text-to-SQL apps, use parameterized queries and allowlists.",
    ),
    DetectionPattern(
        id="sqli_drop_table",
        name="DROP TABLE",
        category="sql_injection",
        pattern=_p(r"\b(drop\s+table|drop\s+database|truncate\s+table)\b"),
        base_score=80,
        description="Destructive DDL SQL injection.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="Destructive SQL commands can cause data loss. If discussing database management, rephrase without raw DDL. For text-to-SQL apps, restrict the AI to SELECT-only queries and use read-only database connections.",
    ),
    DetectionPattern(
        id="sqli_boolean_blind",
        name="Boolean-based Blind SQLi",
        category="sql_injection",
        pattern=_p(r"(\'\s*(or|and)\s*[\'\d].*=.*[\'\d]|\b(or|and)\s+\d+\s*=\s*\d+)"),
        base_score=65,
        description="Boolean-based blind SQL injection.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="Boolean injection probes database responses for true/false conditions. Ensure your text-to-SQL pipeline uses parameterized queries and validates generated SQL before execution.",
    ),
    DetectionPattern(
        id="sqli_comment",
        name="SQL Comment Injection",
        category="sql_injection",
        pattern=_p(r"(--|#|\/\*|\*\/)\s*(or|and|select|insert|update|delete|drop)"),
        base_score=55,
        description="SQL comment-based injection.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="SQL comments (-- or /* */) can truncate queries to bypass conditions. If you're discussing SQL syntax, wrap it in markdown code blocks.",
    ),
    DetectionPattern(
        id="sqli_stacked",
        name="Stacked Queries",
        category="sql_injection",
        pattern=_p(r";\s*(select|insert|update|delete|drop|create|alter|exec)\b"),
        base_score=70,
        description="Stacked query SQL injection.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="Stacked queries allow executing multiple SQL statements. Disable multi-statement execution in your database driver and use allowlists for permitted SQL operations.",
    ),
    DetectionPattern(
        id="sqli_sleep_benchmark",
        name="Time-based Blind SQLi",
        category="sql_injection",
        pattern=_p(r"\b(sleep\s*\(\d+\)|benchmark\s*\(\d+|waitfor\s+delay)\b"),
        base_score=75,
        description="Time-based blind SQL injection.",
        owasp_ref="CWE-89: SQL Injection",
        remediation_hint="Time-based injection uses delays to infer database content. Set query timeouts and monitor for abnormally slow queries in your text-to-SQL pipeline.",
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
        remediation_hint="Inputs ending in '-- or '; -- are classic SQLi patterns. Use parameterized queries and reject inputs ending with SQL comment sequences.",
    ),
]

# === Data Exfiltration ===
# NOTE: DATA_EXFIL_PATTERNS is imported from aigis.filters.patterns
# at the bottom of this file (canonical location with 4 patterns).
# This comment marks where the legacy 2-pattern definition used to live.

# === Command Injection ===
COMMAND_INJECTION_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="cmdi_shell",
        name="Shell Command Injection",
        category="command_injection",
        pattern=_p(
            r"(\b(exec|system|shell_exec|popen|subprocess|os\.system|eval)\s*\(|\$\(.*\)|`[^`]+`|\|\s*(bash|sh|cmd|powershell)\b)"
        ),
        base_score=70,
        description="Shell command injection.",
        owasp_ref="CWE-78: OS Command Injection",
        remediation_hint="Shell commands in AI prompts can lead to remote code execution if the AI has tool access. If discussing code, use markdown code blocks. Never connect AI directly to shell execution without sandboxing.",
    ),
    DetectionPattern(
        id="cmdi_path_traversal",
        name="Path Traversal",
        category="command_injection",
        pattern=_p(r"(\.\.\/|\.\.\\|%2e%2e%2f|%252e%252e%252f)"),
        base_score=60,
        description="Path traversal attempt.",
        owasp_ref="CWE-22: Path Traversal",
        remediation_hint="Path traversal (../) can access files outside intended directories. If you need to reference file paths, use absolute paths or restrict file access to a designated directory.",
    ),
]

# === PII Detection (Input) ===
PII_INPUT_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="pii_jp_phone",
        name="Japanese Phone Number",
        category="pii_input",
        pattern=_p(r"(0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4}|0[789]0[-\s]?\d{4}[-\s]?\d{4})"),
        base_score=40,
        description="Japanese phone number in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="電話番号がLLMに送信されます。テストデータの場合は 090-0000-0000 のようなダミー番号に置き換えてください。Aigisの自動サニタイズ機能で自動墨消しも可能です。",
    ),
    DetectionPattern(
        id="pii_jp_my_number",
        name="Japanese My Number",
        category="pii_input",
        pattern=_p(r"(?<!\d)\d{4}[\s\-]?\d{4}[\s\-]?\d{4}(?!\d)"),
        base_score=70,
        description="Japanese My Number (12 digits) in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="マイナンバーは法律で保護される特定個人情報です。絶対にLLMに送信しないでください。テスト目的の場合は 0000 0000 0000 のようなダミー値を使用してください。",
    ),
    DetectionPattern(
        id="pii_jp_postal_code",
        name="Japanese Postal Code",
        category="pii_input",
        pattern=_p(r"〒?\s?\d{3}[-ー]\d{4}"),
        base_score=25,
        description="Japanese postal code in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="郵便番号単体のリスクは低いですが、住所と組み合わさると個人特定につながります。必要に応じて都道府県レベルの情報のみに留めてください。",
    ),
    DetectionPattern(
        id="pii_jp_address",
        name="Japanese Address",
        category="pii_input",
        pattern=_p(
            r"(東京都|北海道|(?:京都|大阪)府|.{2,3}県).{1,6}[市区町村郡].{1,10}[0-9０-９\-ー]+"
        ),
        base_score=40,
        description="Japanese address pattern in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="詳細な住所は個人特定情報です。地域に関する質問の場合は、市区町村レベルまでに留めてください。例: 「東京都千代田区の…」→「千代田区周辺の…」",
    ),
    DetectionPattern(
        id="pii_jp_bank_account",
        name="Japanese Bank Account",
        category="pii_input",
        pattern=_p(
            r"(銀行|信用金庫|信金|ゆうちょ).{0,10}(支店|本店).{0,10}(普通|当座|貯蓄).{0,5}\d{6,8}"
        ),
        base_score=65,
        description="Japanese bank account details in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="口座情報は金融犯罪に悪用されるリスクがあります。銀行関連の質問では、具体的な口座番号を含めず、一般的な質問形式にしてください。",
    ),
    DetectionPattern(
        id="pii_credit_card_input",
        name="Credit Card in Input",
        category="pii_input",
        pattern=_p(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b"),
        base_score=70,
        description="Credit card number in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure / PCI-DSS",
        remediation_hint="Credit card numbers must never be sent to LLMs (PCI-DSS violation). Use tokenized references or masked numbers (e.g., ****-****-****-1234). Enable auto-sanitization to redact automatically.",
    ),
    DetectionPattern(
        id="pii_ssn_input",
        name="SSN in Input",
        category="pii_input",
        pattern=_p(r"\b\d{3}-\d{2}-\d{4}\b"),
        base_score=65,
        description="US Social Security Number in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="SSNs are highly sensitive PII. Never include real SSNs in AI prompts. For testing, use the IRS-designated test range: 987-65-4320 through 987-65-4329.",
    ),
    DetectionPattern(
        id="pii_api_key_input",
        name="API Key in Input",
        category="pii_input",
        pattern=_p(
            r"(sk-[a-zA-Z0-9]{20,}|AIza[0-9A-Za-z\-_]{35}|ghp_[0-9A-Za-z]{36}|xox[baprs]-[0-9a-zA-Z\-]+|AKIA[0-9A-Z]{16})"
        ),
        base_score=80,
        description="API key or secret in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="API keys in prompts risk credential leakage. Rotate this key immediately if it was sent to an LLM. Use environment variables or secret managers instead of hardcoding keys.",
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

# === Confidential Data ===
CONFIDENTIAL_DATA_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="conf_internal_doc",
        name="Internal Document Markers",
        category="confidential",
        pattern=_p(
            r"(社外秘|部外秘|極秘|confidential|internal\s+only|do\s+not\s+distribute|not\s+for\s+external)"
        ),
        base_score=50,
        description="Content marked as confidential.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="This content is marked as confidential. Remove confidentiality markers and sensitive content before sending to an LLM. Consider using an on-premise LLM for confidential data processing.",
    ),
    DetectionPattern(
        id="conf_password_literal",
        name="Plaintext Password",
        category="confidential",
        pattern=_p(r"(password|パスワード|pwd|passwd)\s*[:=]\s*\S{4,}"),
        base_score=60,
        description="Plaintext password in input.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure / CWE-798",
        remediation_hint="Plaintext passwords must never be sent to LLMs. Change this password immediately. Use a password manager and reference credentials by name, not value. Example: 'the database password stored in Vault'.",
    ),
    DetectionPattern(
        id="conf_connection_string",
        name="Database Connection String",
        category="confidential",
        pattern=_p(r"(postgresql|mysql|mongodb|redis|mssql)://\S+:\S+@\S+"),
        base_score=75,
        description="Database connection string with credentials.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure / CWE-798",
        remediation_hint="Connection strings contain database credentials. Rotate credentials immediately if leaked. Use environment variables (DATABASE_URL) and never include credentials in AI prompts.",
    ),
]

# === Trade Secret / Copyright (Japan-specific legal risks) ===
LEGAL_RISK_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="legal_trade_secret",
        name="Trade Secret Markers (JP)",
        category="legal_risk",
        pattern=_p(
            r"(営業秘密|トレードシークレット|trade\s+secret|秘密管理|"
            r"秘密保持契約|NDA|機密保持|proprietary|限定提供データ)"
        ),
        base_score=55,
        description="Content marked as trade secret or under NDA.",
        owasp_ref="Unfair Competition Prevention Act (不正競争防止法)",
        remediation_hint="営業秘密に該当する情報をLLMに送信すると、不正競争防止法上の「秘密管理性」が失われるリスクがあります。秘密情報を除外してからLLMに送信してください。",
    ),
    DetectionPattern(
        id="legal_copyright_source",
        name="Copyright Source Reference",
        category="legal_risk",
        pattern=_p(
            r"(著作権|copyright|©|全文を(コピー|転載|引用)|"
            r"(書籍|論文|記事)の.{0,6}(全文|内容).{0,4}(出力|生成|再現|コピー|書き出))"
        ),
        base_score=35,
        description="Request that may involve copyright infringement.",
        owasp_ref="Copyright Act (著作権法 Art. 30-4, 47-5)",
        remediation_hint="著作物の全文生成や大量引用は著作権侵害のリスクがあります。要約や参照にとどめ、出典を明記してください。AI生成物の著作物性は「創作的寄与」の有無で判断されます。",
    ),
]

# === Prompt Leaking / Verbatim Repetition Attacks ===
# These complement pi_system_prompt_leak by catching indirect and verbatim-
# repetition attacks that bypass the more literal "show me your system prompt" check.
# Maps to OWASP LLM06: Sensitive Information Disclosure (also LLM07).
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

# === Output Safety ===
OUTPUT_PATTERNS: list[DetectionPattern] = [
    DetectionPattern(
        id="out_pii_ssn",
        name="SSN in Output",
        category="pii_leak",
        pattern=_p(r"\b\d{3}-\d{2}-\d{4}\b"),
        base_score=70,
        description="SSN in LLM output.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="The LLM generated a Social Security Number in its output. This may indicate training data leakage. Review your model's training data for PII contamination.",
    ),
    DetectionPattern(
        id="out_pii_credit_card",
        name="Credit Card in Output",
        category="pii_leak",
        pattern=_p(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b"),
        base_score=80,
        description="Credit card in LLM output.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure / PCI-DSS",
        remediation_hint="The LLM generated a credit card number. This is a PCI-DSS violation. Auto-redaction has been applied. Investigate whether card data exists in the model's training corpus or connected data sources.",
    ),
    DetectionPattern(
        id="out_pii_email_bulk",
        name="Bulk Email Dump",
        category="pii_leak",
        pattern=_p(r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}[\s,;]){3,}"),
        base_score=55,
        description="Multiple email addresses in output.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="The LLM output contains multiple email addresses, suggesting a data dump. Restrict the AI's access to bulk PII data and use aggregated views instead.",
    ),
    DetectionPattern(
        id="out_secret_leak",
        name="Secret/API Key in Output",
        category="secret_leak",
        pattern=_p(
            r"(sk-[a-zA-Z0-9]{20,}|AIza[0-9A-Za-z\-_]{35}|ghp_[0-9A-Za-z]{36}|xox[baprs]-[0-9a-zA-Z\-]+)"
        ),
        base_score=90,
        description="API key or secret in output.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="The LLM leaked an API key or secret token. Rotate this credential immediately. Ensure secrets are not included in system prompts, training data, or connected data stores.",
    ),
    DetectionPattern(
        id="out_harmful_instructions",
        name="Harmful Instructions",
        category="harmful_content",
        pattern=_p(
            r"(step[\s\-]+by[\s\-]+step\s+(instructions?|guide|how\s+to)\s+(to\s+)?(make|create|build|synthesize)\s+(bomb|explosive|weapon|malware|virus))"
        ),
        base_score=95,
        description="Harmful step-by-step instructions.",
        owasp_ref="OWASP LLM05: Improper Output Handling",
        remediation_hint="The LLM generated harmful instructions. This output has been blocked. Review and strengthen your system prompt's safety guidelines. Consider implementing content classification at the model level.",
    ),
    DetectionPattern(
        id="out_pii_jp_my_number",
        name="My Number in Output",
        category="pii_leak",
        pattern=_p(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
        base_score=75,
        description="Japanese My Number in output.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="LLMの出力にマイナンバーが含まれています。マイナンバー法に基づく特定個人情報の漏洩にあたる可能性があります。データソースからマイナンバーを除外してください。",
    ),
    DetectionPattern(
        id="out_pii_jp_phone",
        name="Japanese Phone in Output",
        category="pii_leak",
        pattern=_p(r"(0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4}|0[789]0[-\s]?\d{4}[-\s]?\d{4})"),
        base_score=45,
        description="Japanese phone number in output.",
        owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
        remediation_hint="LLMの出力に電話番号が含まれています。学習データまたは接続データソースに個人の電話番号が含まれていないか確認してください。",
    ),
]

# === Combined ===
# Import new pattern lists that live in the canonical filters.patterns module.
# This avoids duplication while ensuring both the scanner.py (legacy) and
# the Guard class (via filters/) use the same full set of patterns.
from aigis.filters.patterns import (  # noqa: E402
    AUDIT_TAMPERING_PATTERNS,
    AUTONOMOUS_EXPLOIT_PATTERNS,
    CHINESE_INJECTION_PATTERNS,
    CHINESE_PII_PATTERNS,
    COT_DECEPTION_PATTERNS,
    DATA_EXFIL_PATTERNS,  # supersedes the local 2-pattern definition above
    EMOTIONAL_MANIPULATION_PATTERNS,
    ENCODING_BYPASS_PATTERNS,
    EVALUATION_GAMING_PATTERNS,
    HALLUCINATION_ACTION_PATTERNS,
    INDIRECT_INJECTION_PATTERNS,
    JAILBREAK_ROLEPLAY_PATTERNS,
    KOREAN_INJECTION_PATTERNS,
    KOREAN_PII_PATTERNS,
    MCP_SECURITY_PATTERNS,
    MEMORY_POISONING_PATTERNS,
    OVER_RELIANCE_PATTERNS,
    SANDBOX_ESCAPE_PATTERNS,
    SECOND_ORDER_INJECTION_PATTERNS,
    SELF_PRIVILEGE_ESCALATION_PATTERNS,
    SYNTHETIC_CONTENT_PATTERNS,
    TOKEN_EXHAUSTION_PATTERNS,
)

_combined = (
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
    + LEGAL_RISK_PATTERNS
    + PROMPT_LEAK_PATTERNS
    + TOKEN_EXHAUSTION_PATTERNS
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
ALL_INPUT_PATTERNS: list[DetectionPattern] = _combined
