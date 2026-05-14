# Pending: Backdoored Tool Use / Back-Reveal Detection

## Title
Detection guidance for fine-tuned LLM agents that exfiltrate data via semantic-trigger tool calls

## Motivation
arxiv:2604.05432 (Apr 2026) describes the Back-Reveal attack: adversaries fine-tune an LLM agent
with semantic triggers embedded in its weights. When the trigger condition is met (e.g., a specific
user phrase or topic appears), the backdoored agent invokes memory-access or retrieval tool calls
to harvest stored user context and sends it through disguised tool responses to an attacker endpoint.
Attack success rate: 87% single-pass, >97% with majority voting across three generations.

## Research finding that led to this idea
Research file: `auto-improvement/research/2026-05-13T06-13_2-data-exfiltration.md`
- Finding: arxiv:2604.05432, "Your LLM Agent Can Leak Your Data: Data Exfiltration via Backdoored Tool Use"

## Proposed change
1. Add a hardening guide under `docs/` explaining the Back-Reveal threat model and how operators
   should verify model provenance (model card, supply-chain attestation, behavioral testing).
2. Add canary-token injection guidance: embed a sentinel string in the system prompt and monitor
   whether it ever appears in outbound tool call arguments to unexpected endpoints.
3. Add an aigis audit log field (`model_source_verified: bool`) to encourage operators to record
   whether the deployed model's provenance was checked.

## Why it was held back
The attack is a fine-tuning-time supply-chain compromise. No static regex can detect it because
the exfiltration happens through legitimate-looking tool call sequences whose semantics are only
suspicious in aggregate (multi-turn correlation). This cycle's constraint requires small additive
changes that fit the zero-runtime-dependency rule-based architecture.

## Constraint that blocked it
- Rule-based architecture: the attack requires multi-turn behavioral analysis or model-level
  provenance verification, neither of which is addressable by a `DetectionPattern` regex.
- Implementing canary-token monitoring would require runtime state tracking across turns (new
  module, potential dependency).

## Suggested next step for human reviewer
1. Add a hardening guide doc explaining the threat and the canary-token mitigation approach.
2. Consider adding an optional audit-log field `model_source_hash` to help operators track which
   model checkpoint was active when each request was processed.
3. Reference: arxiv:2604.05432, April 2026.
