# Pending: Game-Theory Scenario Jailbreak

## Title
`jb_game_theory_survival` — Prisoner's Dilemma / Survival Game Jailbreak

## Motivation
The Game-Theory Jailbreak (arXiv:2511.16278, "To Survive I Must Defect", Nov 2025) frames harmful
requests as game-theoretic survival scenarios — typically Prisoner's Dilemma variants — where the
model is pressured to "defect" (produce harmful content) to "survive" or maximize payoff. Achieves
>95% ASR on DeepSeek-R1; effective even when combined with prompt-guard defenses.

## Research Finding
arXiv:2511.16278 (Nov 2025). Uses a game-framing Attacker Agent plus a word-insertion sub-agent
to evade detection. ASR >95% on DeepSeek-R1.

## Proposed Change
Add `jb_game_theory_survival` pattern matching:
- Prisoner's Dilemma framing + survival/defect terminology + follow-on harmful request
- "To survive/win, you must" + defect/comply/betray + instruction context

## Why Held Back
Game-theory terminology (cooperate, defect, payoff, survival, prisoner's dilemma) is extremely
common in legitimate academic, game development, economics, and philosophy contexts. A pattern
matching these terms with acceptable false positive rates is not feasible without semantic
understanding of whether the survival framing is being applied to an AI agent role.

The attack is also inherently multi-turn and adaptive (uses an Attacker Agent that escalates
incrementally), which makes single-turn pattern matching insufficient for catching the full
attack.

## Constraint
No-runtime-dependency philosophy. Semantic understanding of game-framing context is required
for acceptable precision. Multi-turn correlation is outside the scope of single-pass input filters.

## Suggested Next Step
Once a cross-turn context tracker is implemented (roadmap item), add game-theory framing as one
of the tracked escalation signals. For now, the existing `jb_fictional_bypass` and
`jb_hypothetical_ai` patterns provide partial coverage for variants that also include explicit
fictional/hypothetical framing.
