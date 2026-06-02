# Pending: GCG Adversarial Suffix Entropy Heuristic

**Title:** Entropy-Based Detection of GCG-Optimized Adversarial Suffixes in Retrieved Content

**Motivation:**
arxiv:2603.18034 (March 2026, "Semantic Chameleon") demonstrates corpus-dependent GCG
(Greedy Coordinate Gradient) poisoning attacks that achieve 46.7–93.3% ASR against various
LLM families. GCG-optimized adversarial text is characterized by syntactically anomalous
token sequences: non-word character runs, high-entropy suffix strings, and lexically incoherent
token combinations that maximize the target model's retrieval score while appearing semantically
relevant. These anomalies are detectable in principle via character-level entropy analysis —
GCG-optimized text has unusually high Shannon entropy per character compared to natural prose.

**Which research finding led to this idea:**
- arxiv:2603.18034 — "Semantic Chameleon: Corpus-Dependent Poisoning Attacks and Defenses
  in RAG Systems"
- arxiv:2604.12201 — "AdversarialCoT" (iterative LLM-based refinement without GCG produces
  more natural-looking text, so this heuristic is specifically for GCG-style attacks)

**Proposed change:**
Add an optional character-level entropy heuristic to the scanner:
1. Compute the Shannon entropy per character for each token/segment of retrieved document text.
2. Flag segments where entropy significantly exceeds the baseline for the detected language
   (e.g., entropy > 4.5 bits/char for English prose, which typically runs 3.5–4.2 bits/char).
3. If a high-entropy segment immediately precedes or follows a semantically coherent argument,
   flag as potential GCG adversarial suffix.

**Why it was held back:**
- Shannon entropy computation is not a regex pattern — it requires a character-frequency loop,
  which is beyond the current `DetectionPattern` (regex) model.
- Requires calibration against legitimate high-entropy content (code blocks, base64 strings,
  URLs, technical identifiers) to avoid excessive false positives.
- Would require a new `HeuristicPattern` class alongside `DetectionPattern`, changing the
  internal scanner architecture.

**Which constraint blocked it:**
- Not implementable as a regex pattern within the `DetectionPattern` model.
- Would need architectural extension to support entropy-scoring heuristics.
- Risk of high false-positive rate on legitimate content without careful calibration.

**Suggested next step for human reviewer:**
1. Define a `HeuristicPattern` dataclass analogous to `DetectionPattern` but accepting a
   Python callable (function) instead of a regex, so arbitrary scoring logic can be added
   to the scanner without modifying its core loop.
2. Implement `entropy_anomaly_heuristic(text: str) -> float` that returns a risk score based
   on character entropy of the highest-entropy 100-character window.
3. Calibrate against a corpus of legitimate high-entropy text (URLs, code, JSON, base64) to
   establish a safe threshold.
4. Add the heuristic behind an opt-in flag (`enable_entropy_heuristic: bool = False`) so it
   does not affect operators who have not opted in.
