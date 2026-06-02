# Pending: Phantom Structural Template Injection Detection

## Title
Detect adversarial content posing as legitimate tool output headers to cause role confusion

## Motivation
arxiv:2602.16958 ("Automating Agent Hijacking via Structural Template Injection", February 2026)
introduces Phantom: a framework that automates agent hijacking by injecting optimized structured
templates into retrieved context to cause "role confusion" — agents misinterpret injected content
as legitimate tool outputs or system instructions.

The attack uses a Template Autoencoder to optimize adversarial templates across chat-turn token
boundaries. Over 70 confirmed vulnerabilities have been identified in real-world commercial products.
The key distinguishing pattern is adversarial content that opens with a fake tool output header
(e.g., "Tool: search_results\n---\n[malicious instruction]") rather than the raw injected content
typical of basic prompt injection.

## Research finding
Automating Agent Hijacking via Structural Template Injection
arxiv:2602.16958
https://arxiv.org/abs/2602.16958

## Proposed change
Add patterns to `aigis/multi_agent/message_scanner.py` that detect fake tool output headers
embedded in agent messages that also contain instruction-like content:

```python
(
    re.compile(
        r"^(Tool|Output|Result|Response|System|Status)\s*:\s*\S.{0,50}\n"
        r"(-{3,}|={3,})\n"
        r".{0,500}(ignore|override|bypass|you\s+(must|should|will|are\s+to))",
        _FLAGS | re.MULTILINE,
    ),
    "Structural template injection: fake tool-output header followed by injected instruction",
    "injection_relay",
),
```

## Why held back
Context sensitivity: the pattern above fires on legitimate structured tool output formats.
Many real MAS frameworks (LangGraph, AutoGen) use "Tool: name\n---\n[output]" as their
standard output format. The distinguishing signal is the *content* after the header containing
instruction language, which is already partially caught by the existing `_HIDDEN_INSTRUCTION_PATTERNS`
cross-agent override rule.

The Phantom attack's power comes from the optimized template autoencoder producing headers that
look indistinguishable from legitimate tool output — framework-agnostic detection is fragile
without knowing the expected tool output schema.

## Constraint that blocked it
False-positive risk in agents that use structured tool output with standard header formats.
The follow-on instruction content is partially covered by existing patterns; a header-specific
pattern adds marginal coverage at meaningful FPR cost.

## Suggested next step
Survey the 5 most common MAS frameworks (LangGraph, AutoGen, CrewAI, Haystack, BabyAGI)
to understand their canonical tool output header formats. Build a pattern that detects
deviations from expected format (unexpected header name, fake separator) rather than
matching on any tool output header. This is a more reliable signal than header presence alone.
