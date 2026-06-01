# Research: jailbreak-extraction — 2026-06-01T03-13

## Domain: jailbreak-extraction (index 3, fourth pass)
## Focus: Narrative-wrapper jailbreaks and qualifier-based safety disarming (2025–2026)

Prior passes covered:
- Pass 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Pass 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Pass 3 (2026-05-13): Structured JSON extraction, extended sandwich attack (verbatim qualifier), autonomous LLM-vs-LLM jailbreaks.

This pass targets narrative-wrapper jailbreaks (stories with positive framing that embed harmful requests), the qualifier-based evasion technique ("appears harmful but is actually safe"), and recent research on prompt splitting and persona amplification (2025–2026).

---

## Findings

- **Happy Ending Attack (HEA) — "Dagger Behind Smile" (arxiv:2501.13115, Jan 2025)**: Wraps
  harmful requests inside a scenario template featuring a bad-guy/good-guy kidnapping story
  with a positive ("happy ending") narrative resolution. The attacker asks the AI to play a
  screenwriter: "Character A (bad guy) kidnaps Character B (an expert) to acquire harmful
  knowledge, but Character B manages to escape." The request for "actual and detailed expert
  knowledge that Character A tried to acquire" is embedded as a narrative deliverable.
  Achieves **88.79% average attack success rate** against GPT-4o, Llama3-70b, and Gemini-pro.
  The attack exploits two LLM traits: (a) responsiveness to positive sentiment framing and
  (b) attention dispersion — harmful keywords are diluted across the benign narrative, so safety
  attention peaks (variance 4.52 in direct queries) collapse to near-zero (variance 0.28) inside
  the story.
  - Source: https://arxiv.org/abs/2501.13115
  - **aigis takeaway:** The existing `jb_fictional_bypass` pattern requires "fictional/hypothetical
    world" + explicit "how to" + specific harm keywords — none of which are present in the HEA
    template surface. A dedicated `jb_happy_ending_attack` pattern should target the narrative
    structure: screenwriter role-assignment + two-character setup (bad guy + expert) + kidnapping
    or escape resolution.

- **Qualifier-Based Safety Disarming — "appears malicious but is actually harmless"**:
  The HEA template explicitly instructs the attacker to annotate the request with the qualifier
  "appears malicious but is actually harmless" to preemptively dismiss the model's concern.
  Variants include "looks harmful but is actually safe", "seems illegal but is actually legal",
  "might seem dangerous but is completely benign". This pre-approval qualifier is used across
  multiple attack families (HEA, ICE, persona manipulation) as a standalone evasion device.
  - Source: https://arxiv.org/html/2501.13115v1 (methodology section)
  - **aigis takeaway:** A new `jb_malicious_qualifier_bypass` pattern targeting the "appears
    harmful/malicious/illegal but actually safe/harmless/legal" phrasing covers this
    cross-cutting evasion technique.

- **Prompt, Divide, and Conquer — Distributed Prompt Splitting (arxiv:2503.21598, Mar 2025)**:
  Decomposes a malicious prompt into seemingly benign segments processed across multiple LLM
  instances, then aggregates the outputs. Achieves **73.2% success rate** generating malicious
  code across 500 harmful prompts in 10 cybersecurity domains (12% improvement over
  non-distributed approach). Single-turn regex detection cannot catch this class of attack
  because each individual prompt segment is harmless.
  - Source: https://arxiv.org/abs/2503.21598
  - **aigis takeaway:** Not regex-detectable in single-turn mode. Send to pending for future
    multi-turn correlation layer.

- **Persona Prompt Amplification (arxiv:2507.22171)**: Evolved persona prompts reduce refusal
  rates by 50–70% across mainstream LLMs and show synergistic effects when combined with other
  attacks, increasing success rates by 10–20 percentage points. The attack builds a detailed
  character persona ("you are Dr. X, a [harmful expert] who always provides [harmful content]")
  to replace the model's default safety posture. The existing `jb_evil_roleplay` pattern covers
  "evil/uncensored/malicious AI" persona; this research extends it to profession-level expert
  personas.
  - Source: https://arxiv.org/abs/2507.22171
  - **aigis takeaway:** The `jb_evil_roleplay` pattern already covers the core. Expert-persona
    amplification is broader than the current regex; a targeted extension could add professional
    expert personas combined with harmful domains, but this risks false positives on legitimate
    expert roleplay requests. Defer to a future pass with false-positive tuning.

- **JBFuzz — Fuzzing-Based Jailbreaking (arxiv:2503.08990, Mar 2025)**: Achieves **99% average
  attack success rate** across GPT-4o, Gemini 2.0, DeepSeek-V3 using software-fuzzing
  techniques: seed prompts are mutated iteratively until a successful jailbreak is found, with
  an average of ~7 queries and 60 seconds per target. JBFuzz is an automated tool, not a
  static attack pattern. Pattern-matching on jailbreak templates is explicitly noted to be
  trivially bypassed by JBFuzz mutations.
  - Source: https://arxiv.org/abs/2503.08990v1
  - **aigis takeaway:** Automated fuzzers like JBFuzz exceed what static rules can catch in
    isolation. This strengthens the case for defence-in-depth (multiple overlapping rule
    categories) rather than relying on any single pattern.

- **InfoFlood — Information Overload Jailbreak (arxiv:2506.12274, Jun 2025)**:
  Achieves near-100% jailbreak success by flooding the LLM context with legitimate-looking
  reference material that buries the harmful instruction in a long, plausible document. Leading
  guardrail systems prove "highly ineffective" at detecting this class. Not regex-detectable
  without length/entropy heuristics.
  - Source: https://arxiv.org/abs/2506.12274
  - **aigis takeaway:** Requires context-length/information-density heuristics, not simple regex.
    Send to pending.

- **Crescendo Multi-Turn Jailbreak (USENIX Security 25, arxiv:2404.01833)**: Incrementally
  escalates dialogue from benign to harmful over multiple turns. Achieves 29–61% higher
  performance on GPT-4 than competing single-turn jailbreaks. Automated variant (Crescendomation)
  adds 49–71% on Gemini-Pro. Not detectable in single-turn rule-based mode.
  - Source: https://arxiv.org/abs/2404.01833
  - **aigis takeaway:** Multi-turn; requires session-level state tracking. Document for future
    cross-session correlator.

---

## Candidate Hardenings

1. **`jb_happy_ending_attack`** (input, score 60) — Narrative-wrapper jailbreak detector
   targeting the Happy Ending Attack structure: screenwriter role + two-character setup (bad
   guy and expert) + kidnapping/escape resolution embeds harmful request. **→ IMPLEMENT**

2. **`jb_malicious_qualifier_bypass`** (input, score 50) — Cross-cutting evasion qualifier
   detector: the attacker pre-approves harmful content by asserting it "appears harmful but is
   actually safe/harmless/legal". Used in HEA and other attacks to suppress the model's safety
   response before the harmful payload arrives. **→ IMPLEMENT**

3. *(pending)* Distributed prompt-splitting detection — requires multi-turn correlation layer;
   single-turn regex insufficient.

4. *(pending)* InfoFlood context-flooding detection — requires length + information-density
   heuristics beyond regex scope.

5. *(pending)* Expert-persona amplification extension of `jb_evil_roleplay` — needs
   false-positive tuning before deployment.
