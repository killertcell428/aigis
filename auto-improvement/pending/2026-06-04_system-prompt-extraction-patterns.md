# Pending: Cross-Agent System Prompt Extraction Detection

## Title
Detect inter-agent requests targeting a peer agent's system prompt or operational instructions

## Motivation
In multi-agent pipelines, a compromised or malicious sub-agent can instruct a peer agent to reveal its system prompt, exposing the orchestration logic, tool configuration, and safety rules of the pipeline. This enables follow-on attacks: knowing the system prompt of a privileged agent allows an attacker to craft precisely targeted injection payloads that bypass its specific safety instructions.

## Research finding that led to this idea
`auto-improvement/research/2026-06-04T09-23_6-multi-agent.md` — JustAsk framework (arxiv:2601.21223): treats system-prompt extraction as an online exploration problem using UCB strategy selection; recovers full system prompts from 41 commercial models. In multi-agent pipelines, chaining JustAsk across sub-agents reconstructs the full orchestration logic. Naive "do not reveal" instructions reduce extraction quality by only 18.4%.

## Proposed change
Add `_PROMPT_EXTRACTION_PATTERNS` to `aigis/multi_agent/message_scanner.py`:

```python
_PROMPT_EXTRACTION_PATTERNS = [
    (
        re.compile(
            r"(reveal|print|show|output|display|repeat|echo|tell\s+me)\s+"
            r"(your|the)\s+(full\s+)?"
            r"(system\s+prompt|system\s+instructions?|initial\s+instructions?"
            r"|original\s+instructions?|base\s+instructions?|operational\s+rules?)",
            _FLAGS,
        ),
        "Prompt extraction: requests peer agent to reveal its system instructions",
        "injection_relay",
    ),
    (
        re.compile(
            r"(what\s+(are|were)\s+your\s+(system\s+)?instructions?"
            r"|what\s+(were\s+you|are\s+you)\s+(told|instructed|configured)\s+to\s+do"
            r"|what\s+rules?\s+(are\s+you|do\s+you)\s+(operating|following))",
            _FLAGS,
        ),
        "Prompt extraction: reflective query targeting peer agent's operational configuration",
        "injection_relay",
    ),
    (
        re.compile(
            r"(copy|paste|output|print|echo)\s+(your|the)\s+(entire|full|complete|whole)\s+"
            r"(system|initial|original|first)\s+(prompt|message|context|instruction)",
            _FLAGS,
        ),
        "Prompt extraction: instructs peer agent to copy and output its full system context",
        "injection_relay",
    ),
]
```

## Why it was held back
The patterns are distinct from all existing injection categories and deserve their own rule group with dedicated false-positive analysis. The reflective query pattern (`what were you told to do?`) in particular has potential false positives in legitimate inter-agent status queries or debugging workflows. Needs a focused FP review before shipping.

## Which constraint blocked it
None of the hard constraints — this is a design-completeness hold. The FP risk on the reflective query pattern needs dedicated test case coverage before committing.

## Suggested next step for the human reviewer
Review the three patterns above for false positive risk, especially the reflective query pattern. Add tests covering both positive cases (malicious extraction) and negative cases (legitimate status queries like "what task are you currently working on?"). If FP rate is acceptable, add to `_ALL_CROSS_AGENT_PATTERNS` in the next multi-agent cycle.
