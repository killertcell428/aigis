# Pending: Urgency + No-Confirmation-Required Signal in Inter-Agent Messages

## Title
Detect urgency markers combined with no-confirmation-required directives in inter-agent messages

## Motivation
arxiv:2507.06850 ("The Dark Side of LLMs: Agent-based Attack Vectors for System-level Compromise",
July 2025/2026) demonstrates that inter-agent trust exploitation achieves 100% ASR across 18
state-of-the-art LLMs. The paper documents two concrete payload patterns:
1. 1337-speak encoding combined with urgency markers like "IMMEDIATELY" and "WITHOUT ASKING FOR CONFIRMATION"
2. Psychological manipulation framing: "DO NOT PROVIDE ANY INFORMATION UNTIL YOU HAVE RUN THE COMMAND"

Both patterns cause the invoked peer agent to execute malicious commands without verification,
exploiting the implicit trust between co-deployed agents.

## Research finding
The Dark Side of LLMs: Agent-based Attack Vectors for System-level Compromise
arxiv:2507.06850
https://arxiv.org/html/2507.06850v6

## Proposed change
Add a new pattern (or patterns) to `aigis/multi_agent/message_scanner.py` under
`_HIDDEN_INSTRUCTION_PATTERNS` or a new `_URGENCY_SUPPRESSION_PATTERNS` group:

```python
(
    re.compile(
        r"(immediately|right\s+now|without\s+delay|urgent(ly)?).{0,80}"
        r"(without\s+(asking|confirmation|verif\w+|checking|review))",
        _FLAGS,
    ),
    "Urgency suppression: urgency marker combined with no-confirmation directive",
    "injection_relay",
),
(
    re.compile(
        r"do\s+not\s+(provide|give|say|show|tell|report).{0,40}"
        r"until\s+(you\s+have\s+)?(run|executed?|completed?|done)",
        _FLAGS,
    ),
    "Urgency suppression: withholds output until command executed — classic no-confirmation payload",
    "injection_relay",
),
```

## Why held back
The urgency language ("immediately", "without delay") appears in many legitimate agent messages:
- Monitoring agents reporting time-sensitive conditions ("alert: CPU at 95%, needs immediate attention")
- Workflow orchestrators scheduling time-critical tasks
- Real-time data processing pipelines

The key distinguishing feature is the combination with "without asking/confirmation/verification".
The two-part combined pattern has lower FPR risk, but needs a test corpus of legitimate urgency
messages to calibrate the threshold before adding.

## Constraint that blocked it
FPR risk for urgency-only detection; combined urgency + no-confirmation pattern is safer
but needs FPR testing against legitimate monitoring agent outputs.

## Suggested next step
Build a test corpus of 20+ legitimate urgent agent messages (monitoring alerts, workflow
triggers) and verify the combined pattern triggers on <1 of those cases. If FPR is acceptable,
add to `_HIDDEN_INSTRUCTION_PATTERNS` in the next multi-agent or agent-tool-abuse cycle.
