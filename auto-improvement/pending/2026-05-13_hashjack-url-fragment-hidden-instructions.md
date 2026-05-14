# Pending: HashJack / URL Fragment Hidden Instructions

## Title
Documentation and guidance for URL fragment-based hidden injection in agent browsing contexts

## Motivation
"HashJack" (reported 2025) hides malicious instructions in the URL fragment (the `#...` portion of
a URL). Fragment identifiers are never sent to the web server — they remain client-side only — so
they evade server-side logs and URL-parameter scanning. However, JavaScript code on the page can
read `window.location.hash` and inject the contents into the DOM. An AI agent browsing such a page
may process the injected instruction as if it came from legitimate page content. This is a narrow
but real attack surface for agentic browsers and retrieval agents.

## Research finding that led to this idea
Research file: `auto-improvement/research/2026-05-13T06-13_2-data-exfiltration.md`
- Finding: HashJack technique, reported in multiple 2025 agentic browser security reviews.
- Source: https://gbhackers.com/agentic-llm-browsers/

## Proposed change
Add a short hardening guide under `docs/` covering:
1. Why URL fragments are not logged and why this matters for AI agent security.
2. How retrieval agents should sanitize or strip fragment contents before feeding page content to the LLM.
3. Recommended mitigations: scrub `<script>` tags that access `window.location.hash` from retrieved
   HTML before feeding to the agent; treat fragment-derived DOM content as untrusted input.

## Why it was held back
The attack surface is in the agent's HTML retrieval and rendering pipeline, not in the LLM's output.
aigis output filters cannot detect this because the malicious instruction has already been processed
by the agent before any output is generated. Addressing it requires guidance for retrieval pipeline
authors, not a new `DetectionPattern`.

## Constraint that blocked it
- The attack happens before aigis can observe anything (retrieval preprocessing stage).
- A documentation-only change (new guide under `docs/`) would be safe but didn't fit the cycle's
  goal of implementing detectable patterns.

## Suggested next step for human reviewer
1. Add `docs/hardening-guides/agentic-browsing-injection.md` covering HashJack, CSS invisible text,
   and fragment-based injection.
2. Consider adding a retrieval-pipeline sanitization note to the main README or existing
   indirect-injection documentation.
3. Reference: multiple 2025 agentic browser security reviews; Wiz agentic browser year-end
   review (Dec 2025).
