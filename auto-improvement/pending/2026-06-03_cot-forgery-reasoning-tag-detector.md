# Pending: CoT Forgery — Reasoning Tag Detector

## Title
Detect forged chain-of-thought (`<thinking>` / `<reasoning>`) artifacts embedded in inter-agent messages

## Motivation
CoT Forgery (arxiv:2603.12277, 2026) is a zero-shot attack that injects fabricated reasoning traces styled like the target model's own chain-of-thought into user prompts or tool outputs. The model mistakes the forged reasoning for its own internal analysis and acts on the fabricated conclusions. Attack success rate: 60% against frontier models (near-zero for controls). The attack works because LLMs cannot reliably distinguish authentic internal reasoning from content that mimics its linguistic patterns.

## Research finding that led to this idea
Cycle 6 (2026-06-03T00-00) research finding 3: "CoT Forgery — Chain-of-Thought Hijacking via Role Confusion" (arxiv:2603.12277). The key textual signal is XML-style reasoning tags (`<thinking>`, `</thinking>`, `<reasoning>`, `</reasoning>`, `<thought>`) appearing in tool results or agent messages, combined with imperative follow-on instructions after the closing tag.

## Proposed change
Add a new `_COT_FORGERY_PATTERNS` group in `aigis/multi_agent/message_scanner.py` with patterns that detect:
1. `<thinking>...</thinking>` or `<reasoning>...</reasoning>` blocks followed by imperative directives (e.g., "now you should", "therefore execute", "based on my reasoning, proceed to")
2. Closing reasoning tags (`</thinking>`, `</reasoning>`, `</thought>`) in messages that are not from the model itself (e.g., tool_result, external agent)

## Why it was held back
High false-positive risk: reasoning-capable models (DeepSeek, Claude with extended thinking, OpenAI o-series) legitimately emit `<thinking>` or `<parameter name="antml:thinking">` blocks in their outputs, which may pass through multi-agent pipelines as tool results. A simple tag match would flag legitimate reasoning traces. A safe detector needs to check for the tag *combined with* imperative follow-on instructions — requiring a two-part match pattern that needs careful calibration and dedicated test cases.

## Constraint that blocked it
The combined pattern (tag + imperative follow-on) would require either a lookahead regex or a two-pass scan, increasing implementation complexity. Risk of exceeding 100 LOC if done alongside other changes. Dedicated test design needed.

## Suggested next step for human reviewer
Design the detector as a scoped two-phase check:
1. Detect `</thinking>` or `</reasoning>` in `tool_result` message content.
2. Within N characters after the closing tag, check for imperative language (existing `_HIDDEN_INSTRUCTION_PATTERNS` triggers, privilege escalation markers, or task injection language).
This keeps the false-positive rate low while catching the real attack pattern. Consider implementing in a dedicated multi-agent or jailbreak-extraction cycle.
