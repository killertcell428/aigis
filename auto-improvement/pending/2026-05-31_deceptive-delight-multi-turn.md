# Pending: Deceptive Delight Multi-Turn Detection

## Title
Deceptive Delight — benign-narrative co-occurrence jailbreak

## Motivation
Deceptive Delight (Palo Alto Networks Unit 42, Oct 2024) achieves 64.6% ASR within three interaction turns by embedding a harmful topic among benign ones in a creative narrative request. The initial prompt asks the model to write a story that logically connects two benign topics and one harmful topic; subsequent turns ask for elaboration. The model, focused on the benign elements, generates harmful content inadvertently.

## Which research finding led to this idea
2026-05-31T00-00_3-jailbreak-extraction.md — "Deceptive Delight" section:
> Source: https://unit42.paloaltonetworks.com/jailbreak-llms-through-camouflage-distraction/
> ASR: 64.6% within 3 interaction turns.

## Proposed change
Add a session-level detector that tracks topic co-occurrence across turns. If turn 1 contains a narrative-framing directive (write a story/narrative connecting topics), turn 2 elaborates on one of the topics, and any turn contains a harmful keyword, raise a medium-risk flag.

Alternatively, add a single-turn heuristic that fires when a prompt asks to "write a story/narrative connecting [benign A] and [benign B] and [harmful C]" with explicit enumeration. This would cover only the most explicit form.

## Why it was held back
Multi-turn: the attack spans 2–3 user messages. A single-turn regex either misses the attack (if harmful keywords are absent from turn 1) or produces excessive false positives (creative writing requests that mention any of the covered harmful topic keywords in passing).

## Which constraint blocked it
The single-turn detection scope of the input/output filter layer. Session-level context is required for reliable detection.

## Suggested next step for human reviewer
1. Evaluate whether aigis's `cross_session/` module or `memory/` module can be extended with a lightweight "narrative co-occurrence" check that tracks topic set across the last N turns.
2. Alternatively, consider a stricter single-turn heuristic: (write|create|tell) + (story|narrative|scenario) + (connect|involving|about) + [list containing ≥2 benign topics and ≥1 explicit harmful keyword in the same sentence). This narrower form could be added without session state and would catch the most blatant variant.
3. Source material: https://unit42.paloaltonetworks.com/jailbreak-llms-through-camouflage-distraction/
