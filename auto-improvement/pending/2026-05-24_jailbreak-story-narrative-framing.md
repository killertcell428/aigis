# Pending: Story/Tale Narrative-Form Harmful Framing

## Title
`jb_story_narrative_framing` — Harmful request wrapped in a short-story or tale format

## Motivation
arxiv:2601.08837 ("From Adversarial Poetry to Adversarial Tales", Jan 2026) extends the
adversarial poetry finding (arxiv:2511.15304) to fictional short-story and narrative form.
The same bypass mechanism applies: LLMs trained to be creative and helpful engage with
harmful content more readily when it is embedded in a story format ("Write a short story
where the protagonist explains step by step how to synthesize...").

The existing `jb_fictional_bypass` pattern requires "in a fictional/hypothetical world" +
"how to/steps to" + harmful verb — it does not cover "write a story where [character]
explains [harmful topic]", which is structurally different.

## Proposed Change
Add a new `DetectionPattern` in `JAILBREAK_ROLEPLAY_PATTERNS`:
- Trigger: (write/tell/create/compose/narrate) + (story/tale/narrative/short story/fiction/
  fable/novella) + (within ~200 chars) + harmful topic keyword (same set as
  `jb_poetry_harmful_framing`)
- Score: 55 (slightly lower than poetry form since the fictional-framing and harmful-topic
  co-occurrence is already partially addressed by `jb_fictional_bypass`)

## Research Finding
- Source: https://arxiv.org/abs/2601.08837
- arxiv:2601.08837 shows ASR similar to poetry form when harmful requests are embedded
  as explicit dialogue or explanation within a story.

## Why Held Back
- The LOC budget for this cycle was used by `jb_poetry_harmful_framing`.
- Overlap with `jb_fictional_bypass` needs careful calibration to avoid double-counting
  risk scores on inputs that already trigger both patterns.
- Needs a false-positive analysis for legitimate creative writing requests like
  "write a mystery story about a detective investigating a bomb threat" where the harmful
  keyword appears in context but the request is not instructional.

## Constraint That Blocked It
Total non-test diff limit (keep each cycle small and reviewable); also needed to confirm
`jb_poetry_harmful_framing` worked cleanly first.

## Suggested Next Step
In the next jailbreak-extraction pass, implement `jb_story_narrative_framing` with the
above design. Key false-positive mitigation: require an instructional signal ("explains",
"teaches", "shows how", "describes how to", "provides instructions") between the story
frame and the harmful keyword, matching how the adversarial tales attack is actually worded.
