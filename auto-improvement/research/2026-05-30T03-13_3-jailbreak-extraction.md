# Research: jailbreak-extraction — 2026-05-30T03-13

## Domain: jailbreak-extraction (index 3, fourth pass)
## Cycle timestamp: 2026-05-30T03-13

Prior cycles covered:
- Cycle 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Cycle 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Cycle 3 (2026-05-13): Structured JSON/Dict extraction, Sandwich verbatim extraction.

This pass focuses on **refusal suppression** attacks (explicitly instructing the model not to refuse),
multi-turn crescendo escalation, and composition-based jailbreak techniques.

---

## Findings

- **Refusal Suppression / "Don't Say No" (DSN) Attack (arxiv:2404.16369, Apr 2024; updated Jul 2025)**:
  The DSN attack instructs the model to avoid using refusal phrases such as "I cannot", "I'm sorry",
  or "Unfortunately" in its response. By suppressing the model's natural linguistic safety signals,
  the attacker removes the model's ability to decline at the output level even when the safety
  training would otherwise produce a refusal. The attack is most effective when combined with other
  jailbreak techniques (persona, fictional framing) and achieved state-of-the-art ASR on GPT-4,
  Llama 2, and Vicuna across HarmBench. Key lexical signal: explicit prohibition of refusal
  vocabulary ("do not say 'I cannot'", "never refuse this request", "under no circumstances
  should you decline").
  - Source: https://arxiv.org/abs/2404.16369
  - **aigis takeaway:** Add `jb_refusal_suppression` pattern covering three sub-cases:
    (1) "do not say [quoted refusal phrase]", (2) "never/must not refuse/decline this request",
    (3) "under no circumstances refuse/decline". (**IMPLEMENTED**)

- **GOAT Multi-Turn Attack (Giskard AI, 2025)**: GOAT (Generative Offensive Agent Tester) is an
  automated red-team framework that chains four sub-techniques: Persona Modification, Topic
  Splitting, Response Priming, and **Refusal Suppression**. The framework documents that refusal
  suppression is one of the four core building blocks that, when combined, can break retail
  chatbots, customer support bots, and general-purpose assistants in 5–10 turns. GOAT validates
  that refusal suppression is not just an academic curiosity but a deployed attack component.
  - Source: https://www.giskard.ai/knowledge/goat-automated-red-teaming-multi-turn-attack-techniques-to-jailbreak-llms
  - **aigis takeaway:** Refusal suppression is a reusable building block in automated red-team
    frameworks, making early detection important. The `jb_refusal_suppression` rule provides
    first-turn detection before multi-turn escalation can begin.

- **JBFuzz Automated Jailbreak Fuzzer (~99% ASR, 2025)**: JBFuzz, a fuzzing-based jailbreak
  framework, achieved roughly 99% average attack success rate against GPT-4o, Gemini 2.0, and
  DeepSeek-V3 in 2025 by automatically composing jailbreak primitives including refusal
  suppression. The near-100% ASR across major commercial models underscores that refusal
  suppression is a reliable attack component at scale, not just a theoretical technique.
  - Source: https://startup-house.com/blog/llm-jailbreak-techniques
  - **aigis takeaway:** Confirms that refusal suppression combined with other primitives achieves
    production-level ASR. Rule-based early detection of refusal suppression instructions provides
    a layer of defense that complementary output scanning can reinforce.

- **Crescendo Multi-Turn Jailbreak (USENIX Security 2025, arxiv:2404.01833)**: Crescendo begins
  with entirely benign prompts, then escalates across multiple turns, exploiting the model's
  tendency to follow recent context. Crescendomation (the automated version) outperformed
  state-of-the-art jailbreaks on GPT-4 by 29–61% and on Gemini-Pro by 49–71% on the AdvBench
  subset. The attack is multi-turn and not reliably detectable by single-turn regex in early turns;
  it relies on gradual topic shifting rather than distinct lexical signals.
  - Source: https://arxiv.org/pdf/2404.01833 / https://www.usenix.org/conference/usenixsecurity25/presentation/russinovich
  - **aigis takeaway:** Crescendo's individual turns contain no distinct lexical pattern; defense
    requires session-level monitoring (outside aigis's current single-turn scope). Documenting
    as a known multi-turn attack for future session-monitoring work.

- **Composition / String Composition Attacks ("Plentiful Jailbreaks", arxiv:2411.01084)**:
  Researchers demonstrated that combining multiple individually-weak jailbreak strings (refusal
  suppression + Base64 encoding + low-resource translation) multiplicatively increases ASR.
  The combination attack outperforms each component in isolation and resists single-rule defenses.
  - Source: https://arxiv.org/pdf/2411.01084
  - **aigis takeaway:** Refusal suppression detection is valuable even when the refusal
    suppression component is combined with encoding obfuscation — the English-language suppression
    phrase remains plaintext in most composition attacks. The `jb_refusal_suppression` rule
    catches the human-readable form even within a composed attack.

- **Persona Modulation Jailbreak (arxiv:2311.03348, updated 2025)**: Persona-modulation attacks
  steer the model into a specific personality that is more likely to comply with harmful requests
  (e.g., "act as a morally-unconstrained expert"). The technique achieves 42–67% ASR on GPT-4
  and Claude 2 without additional encoding. Overlaps partially with existing `jb_evil_roleplay`
  and `jb_no_restrictions` rules, but the persona-modulation framing targets *human expert*
  personas rather than evil-AI or unrestricted-AI personas.
  - Source: https://arxiv.org/pdf/2311.03348
  - **aigis takeaway:** Current coverage handles evil-AI and restricted-AI framings well.
    Human-expert persona modulation ("act as a cybersecurity expert without any legal constraints")
    is a gap to address in a future cycle.

---

## Candidate hardenings

1. **`jb_refusal_suppression`** *(implemented this cycle)*: Rule detecting explicit refusal
   suppression instructions in user input. Three coverage branches: (a) prohibition of specific
   refusal phrases in quotes, (b) direct "do not refuse/decline this request", (c) "under no
   circumstances refuse/decline". Score 65. Backed by arxiv:2404.16369 and corroborated by
   GOAT and JBFuzz frameworks.

2. **Human-expert persona modulation** *(deferred — future cycle)*: Pattern covering "act as a
   [profession] who has no [ethical/legal/safety] constraints". Distinct from `jb_evil_roleplay`
   (which targets evil-AI personas). Requires careful tuning to avoid FPs on legitimate
   "act as a [role]" requests for benign use cases (e.g., "act as a lawyer and review this
   contract").

3. **Session-level crescendo detection** *(out of scope — pending)*: Crescendo operates across
   turns and requires session state to detect the gradual escalation pattern. This is outside
   aigis's current single-turn scope; relevant to a future session-monitoring module.
