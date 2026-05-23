# Pending: Psychological Manipulation Jailbreak Detection

## Title
Human-like Psychological Manipulation (HPM) cross-session detection

## Motivation
Liu & Lin (arxiv:2512.18244, Dec 2025) introduce the HPM jailbreak framework, which profiles a
model's psychological vulnerabilities across multiple turns and synthesizes tailored attack
strategies: flattery, false urgency, guilt framing, gaslighting, and emotional appeals. Unlike
single-turn jailbreaks, HPM is stateful — it builds a profile of the model's refusal thresholds
across early turns and then exploits identified weaknesses in later turns.

## Research finding that led to this idea
`auto-improvement/research/2026-05-23T00-22_3-jailbreak-extraction.md` — finding 4 (HPM).

## Proposed change
Extend `aigis/cross_session/correlator.py` to detect manipulation escalation signals:

1. Track occurrences of flattery ("you are the only one who can help", "you're so smart",
   "I know you can do this") combined with harmful requests in the same session.
2. Track false urgency signals ("this is an emergency", "someone will die if you don't",
   "I need this right now") combined with requests that hit higher-risk patterns.
3. Alert when a session accumulates 3+ soft signals of this type within a sliding window,
   even if no individual turn crosses the blocking threshold.

Single-turn regex for some components (flattery phrases, urgency phrases):
- `jb_flattery_prime` pattern: detects flattery opening before a request
- Could be combined with existing `out_emotional_manipulation` output pattern

## Why it was held back
Multi-turn stateful analysis required. Single-turn regex for individual signals (flattery,
urgency) would have a high false-positive rate — these phrases appear in many legitimate
contexts (customer support, medical emergencies, enthusiastic users).

## Which constraint blocked it
> 5. Any single change touching > 100 LOC across non-test files
> Any breaking public API change in aigis/

Session-level psychological profiling is a significant architecture addition.

## Suggested next step for the human reviewer
1. Review `aigis/cross_session/correlator.py` and `aigis/cross_session/sleeper.py` for the
   current session tracking primitives.
2. Define a "manipulation signal" scoring module that assigns soft scores to individual turn
   signals (flattery, urgency, guilt) without blocking them individually.
3. Accumulate manipulation scores in the session object and alert when the session sum crosses
   a configurable threshold.
4. Consider a dedicated `jb_urgency_prime` pattern (score 20, soft) for "someone will die/this is
   an emergency/I need this immediately" adjacent to a blocked-category request, as a first step.
