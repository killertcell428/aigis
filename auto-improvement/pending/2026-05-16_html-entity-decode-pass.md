# Pending: HTML Entity Decode Pass for Web-Agent Pipelines

**Date:** 2026-05-16
**Research finding:** auto-improvement/research/2026-05-16T00-00_7-evasion-obfuscation.md (finding 5)
**Domain:** evasion-obfuscation (#7)

---

## Title

Apply html.unescape() before keyword matching in web-agent / MCP browser-tool content pipelines.

## Motivation

Lasso Security red-teamed Perplexity's BrowseSafe guardrail in January 2026, achieving 36%
bypass using HTML entity-encoded instructions (&#105;&#103;&#110;&#111;&#114;&#101; = "ignore")
hidden in fetched web content. In-Browser LLM Fuzzing (arxiv:2510.13543) showed that by the
10th fuzzing iteration, agentic browser defenses fail in 58–74% of cases using entity mutation
strategies. Palo Alto Unit 42 confirmed HTML entity encoding in real-world indirect prompt
injection attacks.

The existing `enc_markdown_hidden` pattern covers CSS/Markdown concealment but does not cover
raw HTML entity encoding.

## Proposed Change

Add an HTML entity decode step as a preprocessing pass in the scanner pipeline for content
flagged as HTML-origin (from MCP browser tools, web fetch tools, etc.). Apply `html.unescape()`
recursively (max 3 iterations, capped to prevent DoS) before passing content to keyword-based
patterns.

Alternatively, add a `DetectionPattern` that matches dense HTML entity sequences:
```python
DetectionPattern(
    id="enc_html_entity_keywords",
    name="HTML Entity-Encoded Attack Keywords",
    category="encoding_bypass",
    pattern=_p(
        r"(?:&#\d{1,5};){4,}"    # 4+ decimal entities in sequence
        r"|(?:&#x[0-9a-fA-F]{1,4};){4,}"  # 4+ hex entities
    ),
    base_score=45,
    ...
)
```

## Why Held Back

HTML entity encoding is a valid part of web content and HTML templates. A pattern matching any
sequence of entities would have high FPR for HTML pages, code examples, and templates that
legitimately use entities. The correct fix is a decode-then-rescan approach, which requires
changes to the scanner pipeline architecture rather than a simple DetectionPattern addition.

This exceeds the ≤100 LOC non-test diff constraint for a single cycle.

## Constraint Blocking

The pipeline architectural change (add a decode pass before pattern matching) touches
`aigis/scanner.py` and `aigis/filters/input_filter.py` in a way that could change existing
scanning behavior. This is a >100 LOC change with behavior implications.

## Suggested Next Step

1. Add a `decode_html_entities` flag to Scanner/Guard that enables a pre-scan html.unescape()
   pass on content with `content_type="html"` or similar metadata.
2. Default: False (backward-compatible).
3. Implement as an opt-in preprocessing step.
4. Minimum: add a simple `enc_html_entity_keywords` DetectionPattern as a signal.
