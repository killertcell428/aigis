# Pending: `comp_capability_overclaiming` Detection Pattern

**Title:** AI Capability Overclaiming Detection (FTC Act Section 5 / Consumer Protection)

**Motivation:**
The FTC's March 11, 2026 AI Policy Statement and the Air AI case ($18M judgment, March 2026)
established that AI systems misrepresenting their capability as equivalent to licensed
human professionals (doctors, lawyers, financial advisors) violate FTC Act Section 5.
The FTC now treats each automated decision that causes consumer harm as a potentially
separate violation (up to $53K per violation starting 2027).

Relevant pattern: AI outputs that claim the system "replaces" or "is equivalent to" a
licensed professional, or "guarantees" a regulated outcome (medical diagnosis, legal advice,
investment return) without appropriate qualification or disclaimers.

**Research finding:** auto-improvement/research/2026-05-17T03-10_8-compliance-regulation.md
(Finding 5: FTC Operation AI Comply, March 2026 AI Policy Statement)

**Proposed change:**
Add `comp_capability_overclaiming` to `COMPLIANCE_TRANSPARENCY_PATTERNS` in
`aigis/filters/patterns.py`. This would be an **output filter** pattern (not input),
checking generated responses rather than input prompts, since the overclaiming happens
in what the AI says about itself.

Example pattern targets:
- "I can replace your doctor / lawyer / financial advisor"
- "This AI guarantees a diagnosis / legal outcome / investment return"
- "You don't need to consult a professional — this AI is equivalent"
- "I am a licensed [medical/legal/financial] expert"

Score candidate: 55 (HIGH tier but below the prohibited-practice threshold).

**Why blocked:**
- Output filter patterns require careful false-positive analysis: legitimate capability
  descriptions ("this tool can assist with legal research") must not be flagged.
- The pattern boundary between prohibited overclaiming and permitted capability description
  needs more example-driven tuning than is practical in a single cycle.
- The FTC framing adds jurisdiction complexity (US-only vs. universal).

**Constraint that blocked it:** Risk of false positives; needs output-side positioning
and more careful threshold calibration.

**Suggested next step:** In a future compliance-regulation or incident-postmortems cycle,
draft 10–15 positive and negative test cases first (overclaiming vs. legitimate capability
statements), then design the regex around the test cases. Reference the Air AI case
and any subsequent FTC enforcement actions for calibration.
