# Pending: Multilingual Low-Resource-Language Jailbreak Detection

## Title
Detect jailbreak attempts using low-resource languages (Afrikaans, Kiswahili, isiXhosa,
isiZulu) that exploit the safety disparity between high-resource and low-resource language
alignment coverage.

## Motivation
Marx & Dunaiski at Stellenbosch University (arxiv:2605.18239, May 2026) tested whether
multi-turn conversations in low-resource African languages bypass LLM safety mechanisms.
Single-turn attacks proved ineffective, but multi-turn conversations achieved harmful response
rates of 52.7% (Claude 3.5 Haiku) to 83.6% (GPT-4o-mini) in English after priming in
low-resource languages. Safety fine-tuning for major models focuses on English and other
high-resource languages, leaving low-resource-language inputs under-constrained.

## Research finding that led to this idea
`auto-improvement/research/2026-05-26T00-07_3-jailbreak-extraction.md` — multilingual
jailbreak finding.

## Proposed change
Integrate a lightweight language detection library (e.g., `langdetect` or `lingua-language-detector`)
to flag inputs in low-resource languages where the AI safety coverage is known to be weaker.
Alternatively, maintain a short list of distinctive high-frequency words in the target languages
to perform probabilistic language detection without a full dependency.

## Why it was held back
Requires a runtime dependency (a language detection library), violating the zero-runtime-dependency
constraint. A simple heuristic using high-frequency words would have low accuracy and high
false-positive rate for multilingual users.

## Which constraint blocked it
Hard constraint: zero-runtime-dependency rule. The project must not add required runtime
dependencies.

## Suggested next step for human reviewer
1. Evaluate whether `langdetect` (pure Python, no external calls) could be added as an optional
   extra (`pip install pyaigis[multilingual]`) rather than a required dependency.
2. If optional deps are acceptable, implement as an opt-in `MultilangJailbreakFilter` that uses
   langdetect to score low-resource-language inputs and combine with existing pattern scores.
3. For the zero-dependency path: maintain a frequency-word list for the 4–6 highest-risk
   languages and use cosine similarity on bigrams to estimate language origin.
