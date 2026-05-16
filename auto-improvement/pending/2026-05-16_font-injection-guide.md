# Pending: Invisible Font Injection Hardening Guide

**Date:** 2026-05-16
**Research finding:** auto-improvement/research/2026-05-16T00-00_7-evasion-obfuscation.md (finding 4)
**Constraint blocking:** Documentation-only change; lower urgency than code changes.

---

## Title

Document the invisible font injection attack vector for developers building LLM agents that fetch external web content or PDFs.

## Motivation

arxiv:2505.16957 ("Invisible Prompts, Visible Threats: Malicious Font Injection in External Resources for Large Language Models", EMNLP 2025) demonstrates that attackers can inject hidden instructions into webpages or documents by manipulating CSS/font code-to-glyph mappings. When an LLM agent fetches the page and processes the text via a tool (e.g., a web reader or PDF extractor), the font substitution causes the agent to "read" a hidden instruction that is completely invisible in the rendered page.

Two attack scenarios documented:
1. **Malicious content relay:** The hidden instruction directs the agent to produce harmful content.
2. **Sensitive data leakage:** Via MCP-enabled tools, the hidden instruction causes the agent to exfiltrate data to an attacker-controlled endpoint.

This attack is not detectable at the Unicode/string level — it operates at the font/rendering layer. aigis cannot catch it with regex patterns on text content. However, developers can mitigate it by validating that retrieved content is plaintext-only before passing it to the LLM.

## Proposed Change

Add a new document to `docs/hardening/font-injection.md` covering:

1. What the attack is (code-to-glyph manipulation via CSS/custom fonts)
2. Which use cases are at risk (web-browsing agents, PDF-processing agents, MCP tools that return rendered document content)
3. Recommended defenses:
   - Extract plain text only (strip HTML, CSS, and font references before passing to LLM)
   - Use a sandbox for rendering (e.g., headless Chromium with font substitution disabled)
   - Validate that tool output matches expected character set before processing
   - Consider aigis's input scanner as a post-extraction layer (catches string-level obfuscation in the extracted text, but not the rendering-layer attack)
4. Reference: arxiv:2505.16957 (EMNLP 2025)

## Why Held Back

1. **Priority:** Documentation-only; no code change required. Lower urgency than live detection rules.
2. **Scope:** The `docs/` directory is sparse currently; a hardening guide would require creating a subdirectory and index. This is a larger task than a single cycle allows alongside a code implementation.

## Suggested Next Step

1. Implement in a documentation-focused cycle, particularly one targeting `compliance-regulation` or `agent-tool-abuse` domain.
2. Could be combined with other tool-call hardening guidance in a broader "Securing LLM Agent Tool Use" guide.
