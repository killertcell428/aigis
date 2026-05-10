# Pending: Mermaid/PlantUML href Exfiltration Detection

## Title
Detect diagram DSL blocks (Mermaid/PlantUML) with embedded external hyperlinks in LLM output

## Motivation
Researcher Adam Logue disclosed (2025-07-30) that indirect prompt injection via Excel can direct
M365 Copilot to hex-encode corporate emails and embed them as the `href` of a Mermaid diagram
node disguised as a UI button. Clicking the button silently exfiltrates stolen data. Microsoft
patched by removing interactive hyperlinks from Mermaid rendered output (Sep 2025). The attack
pattern extends to PlantUML and D2 diagram DSLs.

Research finding: `auto-improvement/research/2026-05-10T06-00_2-data-exfiltration.md`

Source: https://www.adamlogue.com/microsoft-365-copilot-arbitrary-data-exfiltration-via-mermaid-diagrams-fixed/
Source: https://www.theregister.com/2025/10/24/m365_copilot_mermaid_indirect_prompt_injection/

## Proposed Change
Add an output pattern that detects Mermaid/PlantUML diagram source blocks containing `href=`
attributes pointing to external URLs:

```python
DetectionPattern(
    id="out_diagram_href_exfil",
    name="Diagram DSL External Hyperlink",
    category="data_exfiltration",
    pattern=_p(
        r"```(?:mermaid|plantuml|d2).{0,5000}href\s*[=:]\s*['\"]?https?://(?!localhost)"
    ),
    base_score=65,
    ...
)
```

## Why Held Back
- The regex must span a multi-line code block and match `href=` inside it.
  The `re.DOTALL` flag is already set in `_p()`, but the pattern needs a bounded scan of the
  code block to avoid catastrophic backtracking.
- Need to validate against false positives: Mermaid nodes can legitimately contain `href=`
  for internal navigation in documentation sites.
- This touches >100 LOC non-test diff boundary risk if combined with proper test coverage.

## Suggested Next Step
Use a two-pass approach: first extract code fences with the language tag, then scan the content
for `href=` to external hosts. Add to `OUTPUT_PATTERNS` with score 65 and a note that
internal/allowlisted hosts should be excluded.
