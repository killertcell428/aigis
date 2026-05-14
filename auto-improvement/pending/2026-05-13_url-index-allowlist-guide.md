# Pending: URL-Index Allowlist Hardening Guide

## Title
Documentation: URL-index approach to blocking agent-generated exfiltration links

## Motivation
OpenAI published a paper (Jan 2026, cdn.openai.com/pdf/dd8e7875...) describing their
mitigation for URL-based data exfiltration from LLM agents. The key insight is: compare
any agent-generated URL against an independent web index. URLs that do not appear in the
index (because they were dynamically constructed by an attacker to contain encoded data)
trigger a user-visible warning or are blocked. This is complementary to, not a replacement
for, regex-based exfiltration detection.

## Research Finding
`auto-improvement/research/2026-05-13T07-30_2-data-exfiltration.md`

Source: https://openai.com/index/ai-agent-link-safety/
Source: https://cdn.openai.com/pdf/dd8e7875-e606-42b4-80a1-f824e4e11cf4/prevent-url-data-exfil.pdf

## Proposed Change
Write `docs/hardening/url-exfil-defense.md` explaining:
1. Why dynamically generated URLs with encoded query params are the primary exfil channel.
2. The URL-index approach: maintaining an allowlist of known-good URL prefixes.
3. How aigis's `out_markdown_img_exfil` and `out_reference_style_markdown_exfil` patterns
   complement infrastructure-level URL indexing.
4. Guidance for operators on combining aigis output filtering with CSP img-src allowlists,
   link-preview blockers, and URL-index verification.

## Why Held Back
- Documentation-only; would not add tests or rules.
- Compliance/docs cycles are a better fit for this type of output.
- The paper was published January 2026; it is recent enough to warrant fresh analysis
  before writing the guide.

## Suggested Next Step
Pick up in a future `compliance-regulation` or `incident-postmortems` cycle. Draft the
guide as `docs/hardening/url-exfil-defense.md`.
