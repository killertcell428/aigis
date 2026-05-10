# Pending: Unicode Tag Block (ASCII Smuggling) Detection

## Title
Detect Unicode Tag Block characters (U+E0000–U+E007F) in LLM input/output

## Motivation
Unicode Tag Block characters (U+E0020–U+E007E) map 1-to-1 to printable ASCII but render as
zero-width glyphs. Attackers embed hidden instructions in these invisible characters that LLMs
read but humans cannot see. Used in EchoLeak (CVE-2025-32711) to bypass Microsoft's XPIA
classifier. arXiv 2603.00164 ("Reverse CAPTCHA", 2026) confirms high attack success rate
against frontier models. AWS and Cisco both published defenses in 2025.

Research finding: `auto-improvement/research/2026-05-10T06-00_2-data-exfiltration.md`

Sources:
- https://aws.amazon.com/blogs/security/defending-llm-applications-against-unicode-character-smuggling/
- https://blogs.cisco.com/ai/understanding-and-mitigating-unicode-tag-prompt-injection
- https://arxiv.org/abs/2603.00164

## Proposed Change
Add a pattern (or pre-filter) in `aigis/filters/input_filter.py` and/or
`aigis/filters/output_filter.py` that flags text containing chars in U+E0000–U+E007F:

```python
import re
_UNICODE_TAG_RE = re.compile(r"[\U000E0000-\U000E007F]")
# If match found, inject high-score finding: "unicode_tag_block_smuggling" (score 80)
```

## Why Held Back
- False-positive risk: some emoji tag sequences (flag emojis use U+E0001, U+E007F) are encoded
  using Tag Block characters for subdivision flags (e.g., 🏴󠁧󠁢󠁥󠁮󠁧󠁿 — England flag). Need to
  allowlist tag sequences that form valid flag emoji (U+E0067 U+E0062 ... U+E007F).
- Requires careful Unicode normalization testing and review of how Python regex handles
  characters above U+FFFF in narrow vs wide builds.
- This is a pre-processing concern, not a simple regex pattern — may need a separate text
  normalization step before pattern matching.

## Suggested Next Step
1. Audit which Python regex engines handle `[\U000E0000-\U000E007F]` correctly.
2. Decide whether to allowlist subdivision flag tag sequences or strip all Tag Block chars.
3. Add as a pre-filter step in `filter_input` / `filter_output` before regex pattern matching,
   returning a `FilterResult` with rule_id `unicode_tag_smuggling` if detected.
