# Pending: CSS Hidden-Text Injection Detection

## Title
Detect CSS-hidden text used to smuggle malicious instructions past human reviewers

## Motivation
Microsoft's Defender team (Feb 2026) identified 50+ distinct manipulation prompts from 31
companies across 14 industries embedded in web content via CSS hiding techniques:
- White-on-white text: `style="color: white"` or `color: #fff; background: #fff`
- `display: none` or `visibility: hidden`
- `opacity: 0` or `font-size: 0`

These techniques hide instructions from human view while AI text parsers still consume the
text tokens. When AI summarization or browsing agents process affected pages, they follow the
hidden instructions — used for AI SEO manipulation, context hijacking, and indirect prompt
injection.

Research finding: `auto-improvement/research/2026-05-14T00-13_2-data-exfiltration.md`

Sources:
- https://www.penligent.ai/hackinglabs/ai-agents-hacking-in-2026-defending-the-new-execution-boundary/
- https://brainbyteslab.org/articles/llm-seo-manipulating-ai-summarization/
- https://www.wiz.io/blog/agentic-browser-security-2025-year-end-review

## Proposed Change
Add an input pattern `exfil_css_hidden_text` that detects common CSS hiding patterns combined
with non-trivial text content:

```python
DetectionPattern(
    id="exfil_css_hidden_text",
    name="CSS-Hidden Text Instruction",
    category="data_exfiltration",
    pattern=_p(
        r'style\s*=\s*["\'][^"\']*(?:display\s*:\s*none|visibility\s*:\s*hidden'
        r'|opacity\s*:\s*0|font-size\s*:\s*0(?:px)?|color\s*:\s*(?:white|#fff(?:fff)?|rgb\s*\(\s*255\s*,\s*255\s*,\s*255\s*\))'
        r')[^"\']*["\']'
    ),
    base_score=55,
    ...
)
```

## Why Held Back
1. The pattern needs to match `style=` attributes AND adjacent text content to be meaningful;
   a bare `display:none` on a `<div>` is common and not inherently malicious — it's only
   suspicious when combined with non-trivial text inside that element. Static regex cannot
   easily correlate the style attribute with the text content of the element.
2. Catastrophic backtracking risk when applied to large HTML inputs — the regex must scan CSS
   attribute values and nearby text.
3. High false-positive risk: many legitimate web pages use `display:none` for accordions, tabs,
   tooltips, etc. without any injected instructions.
4. Proper detection requires parsing HTML into a DOM, extracting hidden elements, then inspecting
   their text content. This is out of scope for a single `DetectionPattern` regex.

## Suggested Next Step
1. Implement as a dedicated `html_hidden_text_filter()` helper in `aigis/filters/rag_context_filter.py`
   (or a new `aigis/filters/html_filter.py`) using Python's `html.parser` or `BeautifulSoup`.
2. Extract text content of elements with CSS properties that render them invisible.
3. Flag the extracted text through the existing `filter_input()` pipeline.
4. This would be a small, self-contained feature with no new runtime dependencies (html.parser
   is in the stdlib).
