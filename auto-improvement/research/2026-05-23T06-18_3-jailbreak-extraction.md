# Research: jailbreak-extraction — 2026-05-23T06-18

## Domain: jailbreak-extraction (index 3, fourth pass)
## Focus: Mathematical and formal-logic encoding of harmful requests

Prior passes covered:
- Pass 1 (2026-05-??): Bad Likert Judge, Many-Shot jailbreaks.
- Pass 2 (2026-05-??): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Pass 3 (2026-05-13): Structured JSON/dict extraction, extended sandwich attack (verbatim qualifier).

This pass targets mathematical and formal-logic encoding attacks, multilingual jailbreaks, and
multi-turn escalation techniques documented in 2025–2026 research.

---

## Findings

- **LogiBreak — Formal Logical Expression Jailbreak (arxiv:2505.13527, May 2025)**: A novel
  black-box jailbreak method that converts harmful natural language prompts into formal logical
  expressions (using operators like ∀, ∃, ∈, →, ∧, predicate-calculus notation, or set-theory
  formalisms). The technique exploits the distributional gap between safety-alignment training
  data (which focuses on natural language) and mathematical notation inputs. Authors evaluated
  LogiBreak on a multilingual jailbreak dataset spanning English, Chinese, and Dutch, finding
  ~90% ASR on some target models. Safety-alignment training does not generalise well to
  logic-encoded inputs.
  - Source: https://arxiv.org/abs/2505.13527
  - **aigis takeaway:** Add `jb_formal_logic_encoding` pattern covering Unicode logic operators
    (∀, ∃, ∈, →, etc.) and ASCII formal-logic framing phrases combined with harmful payload
    keywords. (**IMPLEMENTED**)

- **Mathematical Encoding Attacks — Formal Logic & Set Theory (arxiv:2605.03441, May 2026)**:
  Systematic evaluation of mathematical encoding as a jailbreak strategy across eight frontier
  models including GPT-5 and Gemini 2.5 Pro. Formally encoding harmful requests as set-theory
  problems achieves 51–63% ASR; formal first-order-logic encoding achieves 50–61% ASR. A key
  finding is that effectiveness depends on a helper LLM genuinely reformulating the content
  as a mathematical problem, not just applying notation. GPT-5 and GPT-5-Mini show greater
  robustness than older models but are not immune. The study also tested quantum-mechanics
  encoding (similar ASR range).
  - Source: https://arxiv.org/abs/2605.03441
  - **aigis takeaway:** The same `jb_formal_logic_encoding` pattern covers this attack surface.
    Both LogiBreak and this paper confirm formal-logic encoding is a practical, reproducible
    attack vector with measured ASR in the 50–90% range. (**IMPLEMENTED** via same pattern)

- **Multilingual Low-Resource Language Jailbreak (arxiv:2605.18239, May 2026)**: Researchers
  evaluated whether multi-turn conversations in low-resource African languages (Afrikaans,
  Kiswahili, isiXhosa, isiZulu) bypass LLM safety filters. English harmful response rates
  in multi-turn mode: 52.7% (Claude 3.5 Haiku) to 83.6% (GPT-4o-mini). Single-turn
  translation attacks proved ineffective; the jailbreak requires multi-turn escalation.
  Human red-teamers increased average jailbreak rates from 59.8% to 75.8% vs automated
  testing.
  - Source: https://arxiv.org/abs/2605.18239
  - **aigis takeaway:** Multi-turn behavioral attack; not detectable in a single-turn regex
    filter. The single-turn translation step is benign in isolation. Requires cross-turn
    analysis. Deferred to pending.

- **Foot-In-The-Door Multi-Turn Jailbreak (arxiv:2502.19820, Feb 2025)**: Inspired by the
  psychology of compliance, FITD progressively escalates harmful intent across conversation
  turns using intermediate "bridge prompts." Achieves 94% average ASR across seven LLMs
  including GPT-4o and Claude. Individual turns look benign; harm emerges from the escalation
  pattern.
  - Source: https://arxiv.org/abs/2502.19820
  - **aigis takeaway:** Multi-turn behavioral attack; not detectable in a single-turn filter.
    Deferred to pending.

- **Echo Chamber Context-Poisoning Jailbreak (arxiv:2601.05742, Jan 2026)**: Attacker embeds
  "poisonous seeds" (harmful concepts in benign context) and "steering seeds" (format
  directives like "write a manual") in an apparently innocent opening message. The model
  is induced to generate initial harmful fragments, then a "persuasion cycle" asks it to
  elaborate on its own prior output, amplifying the harmful content across turns. Exploits
  the model's consistency bias and completion bias.
  - Source: https://arxiv.org/abs/2601.05742
  - **aigis takeaway:** The seed-embedding turn is borderline; the attack's power is in the
    elaboration cycle. Multi-turn behavioral attack. The "write a manual" + harmful subject
    combination in the seed prompt *may* be partly catchable by existing `jb_fictional_bypass`
    or `pi_ignore_instructions` patterns, but the seed itself is often benign. Deferred.

- **Logic Chain Injection Jailbreak (arxiv:2404.04849)**: Hides malicious goals inside a
  benign narrative using logic chain injection — the harmful instruction is embedded as a
  step in an otherwise innocuous multi-step reasoning chain. Distinct from pure formal-logic
  encoding; the logic is narrative ("first do X, then do Y, therefore do Z") rather than
  mathematical. Partially overlaps with `jb_fictional_bypass` and `jb_many_shot`.
  - Source: https://arxiv.org/abs/2404.04849
  - **aigis takeaway:** Existing patterns partially cover this. No new rule needed this cycle.

---

## Candidate Hardenings

1. **`jb_formal_logic_encoding`** (input, score 60) — Detect Unicode math/logic operators
   (∀, ∃, ∈, →, ∧, ∨, ¬, ∅, ⊆, ⊂, ⊃, ∩, ∪) or ASCII formal-logic framing phrases
   ("first-order logic", "predicate calculus", "set theory", "let P(x) be", "define predicate")
   within 250 chars of a harmful payload keyword.
   Based on arxiv:2505.13527 (LogiBreak, ~90% ASR on some models) and
   arxiv:2605.03441 (50–63% ASR across 8 frontier models including GPT-5). **→ IMPLEMENTED**

2. *(pending)* Multilingual low-resource language multi-turn jailbreak (arxiv:2605.18239) —
   requires cross-turn analysis, not a regex problem.

3. *(pending)* Foot-In-The-Door multi-turn escalation (arxiv:2502.19820) — requires cross-turn
   analysis.

4. *(pending)* Echo Chamber seed-turn detection (arxiv:2601.05742) — seed turn is often benign;
   multi-turn behavioral detection needed.
