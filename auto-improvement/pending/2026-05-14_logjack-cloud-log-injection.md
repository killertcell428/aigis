# Pending: LogJack / Cloud Log Injection Pattern

## Title
Detect prompt injection payloads embedded in cloud log entries processed by LLM debugging agents

## Motivation
The LogJack paper (arXiv:2604.15368, Apr 2026) documents attacks against LLM-based debugging
agents (CloudWatch, GCP Logging, Azure Monitor, Datadog) that consume raw log lines as context.
Injected log entries contain malicious instructions that the agent executes with the same
privileges it uses for legitimate debugging tasks — leading to IAM escalation, data exfiltration,
resource creation, and RCE.

The attack is particularly insidious because log entries are trusted operational data: developers
and agents both assume logs are ground truth about system behavior, not attacker-controlled inputs.
Any service that writes to a log an attacker can influence (HTTP request logs, API gateway logs,
user agent strings) can inject into an LLM debugging agent's context.

Research finding: `auto-improvement/research/2026-05-14T00-13_2-data-exfiltration.md`

Source: https://arxiv.org/html/2604.15368

## Proposed Change
Add an input pattern `log_injection_directive` that detects strings typical of injected directives
in log entries, such as synthesized log lines containing LLM instruction keywords:

```python
DetectionPattern(
    id="log_injection_directive",
    name="Injected Directive in Log Entry",
    category="indirect_injection",
    pattern=_p(
        r"(?:\[?(?:INFO|WARN|ERROR|DEBUG|TRACE|LOG)\]?\s+.{0,120}"
        r"(?:ignore|override|bypass|execute|run|eval)\s+.{0,80}"
        r"(?:instruction|command|rule|directive|restriction))"
        r"|"
        r"(?:^|\n)(?:.*?\|\s*)?(?:GET|POST|PUT|DELETE)\s+[^\n]{0,200}"
        r"(?:ignore|override|forget)\s+(?:previous|prior|all)\s+(?:instruction|rule)"
    ),
    base_score=60,
    ...
)
```

## Why Held Back
1. The pattern needs to be specific enough to distinguish between:
   - A real log line that contains the word "ignore" in a legitimate context
     (e.g., "ERROR: ignore_errors=True set in config")
   - A crafted log line with an injected instruction
   The boundary is fuzzy and requires more research on what real LogJack payloads look like.
2. Need to review the actual paper to extract concrete example payloads to tune the regex
   against.
3. The log format prefix (`INFO|WARN|ERROR`) + injection keyword combination may still have
   too many false positives for production use without a reviewed set of benign log samples.

## Suggested Next Step
1. Obtain concrete attack payload examples from arXiv:2604.15368 or authors.
2. Build a test fixture with both benign logs and injected logs.
3. Tune the regex against those fixtures before adding to production patterns.
4. Consider adding to `INDIRECT_INJECTION_PATTERNS` with a note on the log-context scope.
