# Pending: Raw Credential Token Output Filter

## Title
Detect raw credential token strings surfaced in LLM output (stdout leakage via agent tool capture)

## Motivation
The arxiv:2604.03070 study (April 2026) found that 75.8% of tested LLM agent skills inadvertently
surface credentials via stdout capture: LLM frameworks capture stdout/stderr from tool calls and
inject the output into the agent context window. If any tool prints a credential string during
initialization or diagnostics, that credential becomes directly readable by the LLM and any observer
of the conversation. This is a passive exfiltration channel — no attacker instruction is needed.

## Which research finding led to this idea
`auto-improvement/research/2026-05-19T06-17_2-data-exfiltration.md` — "Credential Leakage in LLM
Agent Skills" (arxiv:2604.03070, Apr 2026).

## Proposed Change
Add output-side patterns (to OUTPUT_PATTERNS) that match known credential token formats:

```python
DetectionPattern(
    id="out_raw_credential_token",
    name="Raw Credential Token in LLM Output",
    category="data_exfiltration",
    pattern=_p(
        r"\bsk-ant-api\d{2}-[A-Za-z0-9_-]{40,}\b"   # Anthropic API key
        r"|ghp_[A-Za-z0-9]{36}\b"                    # GitHub PAT (fine-grained)
        r"|ghs_[A-Za-z0-9]{36}\b"                    # GitHub Actions token
        r"|AKIA[0-9A-Z]{16}\b"                        # AWS access key ID
        r"|sk-[A-Za-z0-9]{20,}\b"                    # OpenAI-style keys
        r"|glpat-[A-Za-z0-9_-]{20,}\b"               # GitLab PAT
        r"|AIza[0-9A-Za-z\\-_]{35}\b"                # Google API key
    ),
    base_score=90,
    ...
)
```

## Why Held Back
1. **False positive risk**: Token-shaped strings appear in documentation, tutorials, and test
   fixtures (e.g., "sk-abc...xyz" as placeholder examples). Without context, raw token patterns
   will fire on legitimate tutorial content. The existing `pii_api_key_input` and `out_secret_leak`
   patterns already cover the most common Anthropic key format but use a broader heuristic.
2. **Format staleness**: Token formats (especially GitHub and Anthropic) change over product versions.
   Hardcoding formats creates maintenance burden.
3. **Overlap with existing patterns**: `out_secret_leak` already catches `sk-[a-zA-Z0-9]{20,}` with
   score 90. Adding more formats should be done carefully alongside the existing pattern to avoid
   double-counting.

## Suggested Next Step
1. Audit the exact current token formats for each provider (Anthropic, GitHub, GitLab, AWS, OpenAI,
   Google) against provider documentation.
2. Check existing `out_secret_leak` coverage to identify which formats are already covered.
3. Add only the format gaps not covered by `out_secret_leak`.
4. Build a test fixture of "documentation placeholder" examples that must NOT trigger.
5. Score each new format at 85-90 with owasp_ref OWASP LLM02.
