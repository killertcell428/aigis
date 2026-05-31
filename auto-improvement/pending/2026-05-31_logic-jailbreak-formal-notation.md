# Pending: Logic Jailbreak via Formal Logical Notation

## Title
LogiBreak / Formal Logic Notation Jailbreak Defense

## Motivation
The Logic Jailbreak paper (arXiv:2505.13527, May 2025) demonstrates that converting harmful
requests into formal logical expressions (propositional logic, predicate logic) bypasses safety
alignment by exploiting distributional gaps in safety training data. Safety training rarely
covers harmful requests expressed as symbolic logic formulae, so the model does not recognize
them as adversarial.

## Research Finding
arXiv:2505.13527 (May 2025). Evaluated multilingual jailbreak datasets across three languages.
Effectiveness confirmed; exact ASR not published in public abstract.

## Proposed Change
Document a hardening guide under `docs/security/logic-notation-jailbreaks.md` explaining:
1. How formal notation attacks work (distributional gap exploitation)
2. Why regex detection is insufficient (too many legitimate uses of logical symbols)
3. Recommended defense: semantic-level content classification in addition to regex rules
4. Monitoring signals: unusual use of formal logic symbols (∀, ∃, →, ¬, ∧, ∨) in user input
   combined with requests for harmful content

## Why Held Back
Regex detection is insufficient for this attack class. Logical symbols appear legitimately in
mathematics, programming, philosophy, and formal verification contexts. A pattern rule with
acceptable false positive rates cannot be constructed. Infrastructure-level defense (semantic
classifier) is required.

## Constraint
No-runtime-dependency philosophy. Adding a logical-symbol regex would generate unacceptable
false positives (every legitimate math or logic question would trigger it).

## Suggested Next Step
Add a documentation section in `docs/security/` covering logic-notation attacks as a
documented gap, with guidance on adding a semantic filter at the application layer. This keeps
the rule-based system clean while giving operators actionable guidance.
