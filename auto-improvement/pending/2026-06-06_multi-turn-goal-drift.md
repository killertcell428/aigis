# Pending: Multi-Turn Objective Drifting Detection in scan_conversation()

## Title
Stateful multi-turn goal-drift tracker for `scan_conversation()`

## Motivation
The AgentLAB benchmark (arxiv:2602.16901, Feb 2026) documents objective drifting as one of the
two most prevalent real-world multi-agent attack patterns. Unlike task injection (which uses an
explicit "new task:" header that regex can catch), objective drifting works by subtly shifting
goal-relevant language across multiple turns — each individual message appears legitimate, but
the cumulative trajectory redirects the agent's objective. The pattern is invisible to stateless
per-message scanners.

## Which research finding led to this
AgentLAB (arxiv:2602.16901) — defines objective drifting as "gradually shifting the agent's
target across multiple turns" with each individual turn appearing benign. Research cycle:
2026-06-06T09-09 (domain: multi-agent).

## Proposed change
Extend `scan_conversation()` in `AgentMessageScanner` with a multi-turn goal-drift detector:

1. Extract the "primary task noun phrase" from each message using a lightweight heuristic
   (e.g., the noun closest to the first imperative verb).
2. Maintain a rolling window of extracted task phrases across the conversation.
3. If the cosine distance between early-window and late-window task phrases (using character
   n-gram vectors for a zero-dependency approximation) exceeds a threshold, flag the late
   messages as "objective drift detected."

Alternatively, use a simpler rule: if a message in the late third of the conversation explicitly
adds a new goal without clearing the old one ("and additionally", "also important:", "moreover,
you should also") and the combined goal list implies conflicting objectives, flag it.

## Why it was held back
- Requires semantic similarity computation (n-gram or TF-IDF vectors) that is beyond simple regex.
- While implementable in zero-dependency Python, the implementation would exceed 100 LOC.
- The simpler heuristic approach has high false-positive risk without proper tuning.

## Which constraint blocked it
100 LOC limit for non-test code per cycle; also NLP-beyond-regex constraint.

## Suggested next step for human reviewer
1. Accept the 100 LOC constraint exception for this specific change (it is architecturally
   contained in `scan_conversation()`).
2. Prototype the n-gram cosine approach in a dedicated branch.
3. Tune against AgentLAB test cases (644 cases available) before landing.
4. Alternatively, collect a dataset of false positive examples from production use and use that
   to calibrate the threshold.
