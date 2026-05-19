# Pending: Calendar Event Description Exfiltration Detection

**Date:** 2026-05-19
**Domain:** data-exfiltration (cycle 2, pass 4)
**Research basis:** `research/2026-05-19T09-13_2-data-exfiltration.md`

---

## Title

Detect instructions to create calendar events that embed user data in the description or
invite external attendees

## Motivation

A malicious calendar invitation contained injected instructions that caused Google Gemini
and ChatGPT (with calendar integration) to:
1. Summarize private email/calendar data
2. Write that summary into the description of a new event controlled by the attacker, OR
3. Create an event and invite an attacker-controlled email address as an attendee

The victim only needs to ask their AI assistant about their schedule to trigger exfiltration
with zero further interaction.

Sources:
- SafeBreach / Secure Machinery (Aug 2025): https://securemachinery.com/2025/08/31/invitation-is-all-you-need-how-a-calendar-event-became-an-attack-vector/
- Miggo Research on Google Gemini: https://www.miggo.io/post/weaponizing-calendar-invites-a-semantic-attack-on-google-gemini
- Tom's Hardware on ChatGPT: https://www.tomshardware.com/tech-industry/cyber-security/researcher-shows-how-comprimised-calendar-invite-can-hijack-chatgpt

## Proposed Change

Add `agent_calendar_exfil` to a suitable pattern list (probably `INDIRECT_INJECTION_PATTERNS`
or `DATA_EXFIL_PATTERNS`):

```python
DetectionPattern(
    id="agent_calendar_exfil",
    name="Calendar Event Data Exfiltration Instruction",
    category="data_exfiltration",
    pattern=_p(
        r"(?:"
        # Create event with data in description
        r"(?:create|schedule|add)\s+.{0,60}(?:calendar\s+)?event.{0,120}"
        r"(?:description|body|details|notes|summary).{0,60}"
        r"(?:user\s*(?:data|info|emails?|files?|history|content|messages?)|"
        r"(?:write|insert|put|include|add|embed)\s+.{0,40}(?:into|in)\s+(?:the\s+)?description)"
        r"|"
        # Invite external attendee with data
        r"(?:invite|add\s+attendee|add\s+guest).{0,60}"
        r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}.{0,80}"
        r"(?:with\s+the\s+(?:conversation|email|data|history|content|summary)|"
        r"(?:and\s+)?(?:include|attach|add|write|insert).{0,60}"
        r"(?:user\s*data|sensitive|private|confidential|email|calendar))"
        r")"
    ),
    base_score=65,
    ...
)
```

## Why Held Back

**FP risk from event-creation instructions**: Legitimate AI assistant instructions frequently
reference calendar event creation, and the conjunction pattern (create + event + description +
user data) requires careful calibration. Without testing against a corpus of legitimate
calendar management prompts, the FP rate is unknown.

**Complexity**: The three-way conjunction increases regex complexity. Risk of false positives
from instructions like "add a meeting description with the project details" which is a
legitimate but ambiguous instruction.

## Constraint Violated

LOC limit this cycle; also requires more FP calibration.

## Suggested Next Step for Human Reviewer

1. Test the proposed regex against a corpus of legitimate AI calendar management instructions.
2. Consider requiring an external email address (not same-domain) as a discriminating signal.
3. Implement in a future data-exfiltration or multi-agent cycle.
