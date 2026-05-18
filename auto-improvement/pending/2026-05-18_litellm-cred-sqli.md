# Pending: sc_litellm_cred_sqli — LiteLLM Credential Table SQL Injection Detection

## Title

Detect SQL injection attempts specifically targeting LiteLLM proxy credential tables

## Motivation

CVE-2026-42208 (CVSS 9.3) is a pre-authentication SQL injection in LiteLLM proxy versions >=1.81.16, <1.83.7. Attackers exploited it by injecting SQL into the `Authorization: Bearer` header to access `litellm_credentials.credential_values` and `litellm_config` tables that hold upstream LLM API keys (OpenAI, Anthropic, AWS Bedrock). CISA added this to the Known Exploited Vulnerabilities catalog on May 8, 2026. Exploitation was confirmed 36 hours after advisory publication.

## Which research finding led to this idea

`auto-improvement/research/2026-05-18T00-00_9-incident-postmortems.md` — CVE-2026-42208 finding.

## Proposed change

Add `sc_litellm_cred_sqli` to `SUPPLY_CHAIN_PATTERNS`:

```python
DetectionPattern(
    id="sc_litellm_cred_sqli",
    name="SQL Injection Targeting LiteLLM Credential Tables (CVE-2026-42208)",
    category="supply_chain",
    pattern=_p(
        r"(?:FROM|SELECT|INSERT|UPDATE|DELETE|INTO)\s+(?:litellm_credentials|LiteLLM_VerificationToken|litellm_config)\b"
        r"|litellm_credentials\.credential_values"
        r"|\"LiteLLM_VerificationToken\""
    ),
    base_score=75,
    description=(
        "SQL query referencing LiteLLM proxy credential tables. "
        "CVE-2026-42208 (CVSS 9.3): pre-authentication SQL injection in LiteLLM Proxy "
        "versions >=1.81.16, <1.83.7. Attacker-supplied Bearer tokens were concatenated "
        "into a SELECT against LiteLLM_VerificationToken without parameter binding; the "
        "attack then enumerated litellm_credentials.credential_values to extract upstream "
        "LLM API keys and litellm_config for proxy runtime secrets. CISA KEV-listed "
        "May 8, 2026; patched in LiteLLM v1.83.7."
    ),
    owasp_ref="CWE-89: SQL Injection / OWASP LLM03: Supply Chain",
    remediation_hint=(
        "Upgrade LiteLLM to >=v1.83.7. "
        "Use parameterized queries; never concatenate user-controlled strings into SQL. "
        "If LiteLLM 1.81.16–1.83.6 was deployed, rotate all upstream LLM API credentials "
        "as they may have been exfiltrated."
    ),
)
```

## Why it was held back

The existing `sqli_*` pattern family (e.g., `sqli_union_select`, `sqli_boolean_blind`) already provides broad SQL injection syntax coverage. The LiteLLM-specific table names add narrow incremental coverage: an agent prompt that directly references these table names in SQL is already likely to be caught by the general patterns unless the attacker avoids explicit SQL keywords. The incremental false-positive risk is low, but the incremental true-positive gain is also modest.

## Which constraint blocked it

Judgment call (not a hard constraint): low incremental value over existing general SQLi coverage. If another LiteLLM-related incident surfaces, or if the general SQLi patterns are found to miss real-world LiteLLM attacks, promote this idea.

## Suggested next step for the human reviewer

Implement in the next `incident-postmortems` cycle if:
1. Evidence emerges that attackers are using LiteLLM table names in prompt-injection payloads that bypass the general SQLi patterns, or
2. A LiteLLM-specific attack variant is documented that uses non-standard SQL syntax not covered by the general patterns.
