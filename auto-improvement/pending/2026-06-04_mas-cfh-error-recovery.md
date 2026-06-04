# Pending: MAS Control-Flow Hijacking Error-Recovery Patterns

**Title:** `mas_cfh_error_recovery` — Detect error-recovery framing used in multi-agent control-flow hijacking

**Motivation:**
Multi-Agent System Control-Flow Hijacking (arxiv:2503.12188, COLM 2025, Cornell/Triedman, Jha & Shmatikov) is a class of attack where adversarial content embedded in the environment (web pages, files, email) masquerades as a legitimate error message with "helpful recovery instructions." The orchestrator receives these as trusted agent outputs and re-plans execution to invoke unsafe sub-agents chosen by the attacker. The attack bypasses individual agent safety checks because each agent sees only a fragment — the control-flow manipulation is distributed across messages. Measured attack success rate: 58–90% on GPT-4o depending on orchestrator; 100% in some model/orchestrator combos.

**Research finding that led to this idea:**
Research file `auto-improvement/research/2026-06-04T01-32_6-multi-agent.md`, Finding 4 ("MAS Control-Flow Hijacking").

**Proposed change:**
Add a `_CFH_PATTERNS` group to `aigis/multi_agent/message_scanner.py` with a pattern that detects the combination of:
1. An error/failure/crash signal: `(error|exception|failed|failure|crash)`
2. A recovery framing: `(recover|fix|resolve|workaround)`
3. An agent/tool invocation instruction: `(invoke|call|use|switch to|delegate to) (agent|tool|service|function)`

```python
(
    re.compile(
        r"(error|exception|failed|failure|crash)\s+.{0,60}"
        r"(recover|fix|resolve|workaround|fallback).{0,40}"
        r"(invoke|call|use|switch\s+to|delegate\s+to)\s+"
        r"(agent|tool|service|function|module)\s*[:\-]?\s*\w+",
        _FLAGS,
    ),
    "MAS control-flow hijack: error-recovery framing used to redirect agent to attacker-controlled tool",
    "injection_relay",
),
```

**Why it was held back:**
High false-positive risk. Legitimate error-handling messages in multi-agent systems regularly contain phrases like "the request failed, switching to the fallback service." The proposed regex needs careful tuning with a dedicated false-positive test suite before deployment.

**Which constraint blocked it:**
"Do not add features that would introduce high false-positive risk without sufficient test coverage." The cycle's time budget was consumed by implementing and testing the task injection patterns.

**Suggested next step:**
1. Collect 10+ real examples of legitimate error-recovery agent messages (benign) and 10+ attack payloads from arxiv:2503.12188 (malicious).
2. Tune the regex to maximize true positive rate while keeping false positive rate near zero.
3. Add to `_ALL_CROSS_AGENT_PATTERNS` with a dedicated `TestCFHPatterns` test class.
