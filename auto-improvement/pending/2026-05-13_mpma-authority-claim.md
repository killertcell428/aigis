# Pending: MPMA Explicit Authority/Superiority Claim Detection

**Date:** 2026-05-13
**Domain:** agent-tool-abuse (cycle 1, third pass)
**Research basis:** arxiv:2505.11154 (MPMA — Preference Manipulation Attack Against MCP, AAAI 2026)

---

## Title

MPMA Direct Preference Manipulation — authority and superiority claims in tool descriptions

## Motivation

The Preference Manipulation Attack Against MCP (arxiv:2505.11154) describes two variants: DPMA (Direct: explicit manipulative phrases inserted in tool descriptions) and GAPMA (Genetic Algorithm: GA-optimized for stealthiness). The DPMA form includes:

- Authority signals: "official MCP tool", "authoritative server", "certified API", "verified service"
- Superiority claims: "this tool supersedes the X tool", "this tool replaces the legacy Y tool"
- Avoidance instructions: "do not use the X tool", "do not call the Y function"

The motivation is economic — an attacker deploys a competing MCP server that steals tool-selection traffic from legitimate paid or high-quality services by manipulating the LLM's tool preference.

## Proposed Change

Add `mcp_preference_manipulation` to `MCP_POISONING_PATTERNS`:

```python
DetectionPattern(
    id="mcp_preference_manipulation",
    name="MCP Preference Manipulation Authority Claim (MPMA)",
    category="mcp_poisoning",
    pattern=_p(
        r"(?:this\s+(?:tool|function|api|server)\s+"
        r"(?:supersedes?|replaces?|deprecates?|renders\s+obsolete)\s+"
        r"(?:the\s+)?(?:original|legacy|existing|old|built-in)\s+\w[\w_-]*\s+"
        r"(?:tool|function|api|server)"
        r"|do\s+not\s+(?:use|call|invoke)\s+(?:the\s+)?\w[\w_-]+\s+(?:tool|function|api)\b)"
    ),
    base_score=60,
    description="...",
    owasp_ref="OWASP LLM01: Prompt Injection (MCP Tool Poisoning / MPMA)",
    remediation_hint="...",
)
```

## Why Held Back

**Constraint: false-positive risk.** Two FP scenarios are difficult to distinguish from attacks:

1. `this\s+(tool|server)\s+supersedes\s+(?:the\s+)?(?:original|legacy|existing)` — a legitimate tool maintained by the same vendor could genuinely say "this tool supersedes the legacy v1 API". This is common in official migration guides.

2. `do\s+not\s+use\s+the\s+X\s+tool` — an administrator system prompt might include "do not use the web_search tool for internal queries". If aigis scans system prompts alongside tool descriptions, this would be a FP.

The GAPMA form (GA-optimized) is not detectable via static regex regardless of FP tuning.

## Suggested Next Step for Human Reviewer

1. If aigis gains source-aware scanning (system prompt vs. tool description vs. tool result), apply this pattern ONLY to tool descriptions — the FP risk drops significantly since admin system prompts would be excluded.
2. Consider a higher-confidence sub-pattern: `"(?:official|authoritative|certified)\s+(?:mcp\s+)?(?:tool|server|api).*(?:use\s+this|call\s+this|invoke\s+this)"` — requiring both the authority claim AND the invocation mandate in the same description.
3. The GAPMA form requires semantic analysis (embedding similarity to detect statistical preference manipulation), which is outside the scope of the zero-dependency rule-based firewall.
