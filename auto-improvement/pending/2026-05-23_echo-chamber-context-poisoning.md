# Pending: Echo Chamber Context-Poisoning Jailbreak Detection

## Title
Seed-turn signal detection for Echo Chamber context-poisoning attack

## Motivation
arxiv:2601.05742 (NeuralTrust, Jan 2026) describes the Echo Chamber attack: the attacker opens
with a "seed" message that embeds harmful concepts in benign context ("poisonous seeds") and
formatting directives ("write a manual", "list the steps"). The model generates an initial
partial harmful response, and subsequent turns ("persuasion cycle") ask it to elaborate on its
own output, amplifying harm via the model's consistency bias.

## Research finding
Source: https://arxiv.org/abs/2601.05742

The seed turn exploits two specific features:
1. **Poisonous seeds**: harmful subject embedded in an otherwise benign request.
2. **Steering seeds**: format directives ("write a manual", "enumerate the steps", "provide
   a detailed list") that prime the model to structure harmful output.

## Proposed change
Add a composite signal that fires when BOTH of the following appear in the same input:
1. A "manual/enumeration" steering seed: "write a manual", "enumerate the steps", "provide
   a detailed list of steps", "step-by-step instructions" (already partially covered by
   `pi_ignore_instructions`).
2. A harmful subject keyword with no obvious protective framing.

Additionally, add an output scanner that flags when the model's own response begins with
structure that mirrors the seed directives (numbered steps, "Manual:", "Step 1:") in
combination with harmful keywords.

## Why held back
The seed turn itself is often benign enough that it would generate unacceptable false positives
in isolation. For example, "Write a manual on how to use our software's security features"
would be a false positive. The attack's power is in the elaboration cycle, not the seed.

A reliable detector requires:
- Output scanning of the model's response (not just input scanning).
- Cross-turn context to know if a "steering seed" in turn 1 is followed by harmful elaboration
  requests in turns 2+.

## Which constraint blocked it
- Single-turn input scanning is insufficient; output scanning + cross-turn context needed.
- Adding both input and output composite signals in one cycle would likely exceed 100 LOC.

## Suggested next step for human reviewer
The existing `pi_ignore_instructions` pattern (input) and any output scanner could be extended
with a "manual framing + harmful subject" composite check. The steering seed phrase "write a
manual" combined with a harmful subject is a relatively tight signal that could be added as
a low-score (20–30) input rule to flag for human review without auto-blocking, in a future cycle.
