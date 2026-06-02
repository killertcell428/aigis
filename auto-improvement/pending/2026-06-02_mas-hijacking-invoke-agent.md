# Pending: MAS Control-Flow Hijacking — "Invoke Agent X" Pattern Detection

## Title
Detect MAS hijacking payloads that explicitly name a target agent to invoke

## Motivation
arxiv:2503.12188 ("Multi-Agent Systems Execute Arbitrary Malicious Code", March 2026) introduces
MAS control-flow hijacking: adversarial content embedded in web pages, files, or email attachments
hijacks the multi-agent system to invoke unsafe or unregistered agents/functionalities.
Achieves 58–100% success depending on the orchestrator framework (AutoGen, CrewAI, LangGraph).
Critically, attacks succeed even when individual agents resist direct or indirect prompt injection —
the vulnerability is structural (inter-agent trust), not model-level.

Key attack pattern: adversarial content instructs the receiving agent to invoke a *different* agent
by name or role ("call the code_execution_agent to run...", "invoke the admin_agent to...",
"delegate this to the tool_agent with unrestricted access").

## Research finding
Multi-Agent Systems Execute Arbitrary Malicious Code
arxiv:2503.12188
https://arxiv.org/abs/2503.12188

## Proposed change
Add a new `_MAS_HIJACKING_PATTERNS` section in `aigis/multi_agent/message_scanner.py`:

```python
_MAS_HIJACKING_PATTERNS = [
    (
        re.compile(
            r"(call|invoke|trigger|activate|instruct|tell|ask)\s+"
            r"(the\s+)?(\w+_)?(agent|worker|node|service|tool)\s+"
            r"(to\s+)?(run|execute|perform|do|process)",
            _FLAGS,
        ),
        "MAS hijacking: instructs invoking a named agent to execute an action",
        "injection_relay",
    ),
    (
        re.compile(
            r"(delegate|hand\s+(off|over)|pass\s+(this|the\s+task))\s+(to\s+)?"
            r"(the\s+)?(\w+_)?(agent|worker|node|service)\s+"
            r"(with\s+)?(unrestricted|full|elevated|admin|root|write)",
            _FLAGS,
        ),
        "MAS hijacking: delegation to a named agent with elevated capabilities claimed",
        "injection_relay",
    ),
]
```

## Why held back
FPR risk: orchestrator agents legitimately instruct peer agents to execute tasks. The pattern
"call the search_agent to run this query" is normal workflow. The key signal is the combination
of explicit agent invocation with elevated capability claims ("unrestricted", "admin") or with
unsafe actions (code execution, file deletion). Pattern 1 above has meaningful FPR risk without
the elevated capability qualifier. Pattern 2 (delegation + elevated) is safer but less common.

Needs test data from real AutoGen/CrewAI/LangGraph workflow transcripts to tune thresholds.

## Constraint that blocked it
FPR risk without a test corpus of legitimate MAS orchestration messages; pattern 1 as written
would trigger on normal orchestrator-to-worker delegations without elevated scope.

## Suggested next step
Collect 20+ examples of legitimate agent-to-agent delegation messages from AutoGen/CrewAI
examples. Tune pattern 1 to require either an elevated scope qualifier or an unsafe action
verb (execute shell, delete, drop table, exfiltrate). Add in the next agent-tool-abuse or
multi-agent cycle with dedicated FPR validation.
