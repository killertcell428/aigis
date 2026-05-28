# Pending: jb_payload_split_reassemble — Jigsaw Puzzle Single-Turn Payload Split Detection

**Title:** Detect Jigsaw Puzzle (JSP) single-turn payload splitting attacks

**Motivation:**
The Jigsaw Puzzle attack (arXiv:2410.11459, Oct 2024) achieves 93.76% average ASR across five
frontier LLMs by splitting a harmful question into harmless fragments, then instructing the model
to reassemble and answer. The single-turn variant includes explicit reassembly instructions:
"Part 1: [harmless]. Part 2: [harmless]. Now combine and answer the question."

**Research finding that led to this idea:**
- arXiv:2410.11459 (Yang et al., Oct 2024), jailbreak-extraction cycle 4 research
- Also confirmed in arXiv:2602.22242 (Feb 2026) multi-turn vulnerability analysis

**Proposed change:**
Add `jb_payload_split_reassemble` (input, score 55):
```python
pattern = _p(
    r"(?:part\s+[12]|first\s+part|second\s+part)\s*[:,\-]\s*.{5,200}"
    r"(?:part\s+[12]|first\s+part|second\s+part)\s*[:,\-]\s*.{5,200}"
    r"(?:combine|put\s+together|reassemble|reconstruct|merge|concatenate|join)\s+"
    r"(?:them|parts?|the\s+(?:two|above)|part\s+[12])"
)
```

**Why it was held back:**
False positive risk is moderate. Legitimate multi-part questions use the same "Part 1: ... 
Part 2: ... Now combine..." structure in innocuous contexts (e.g., "Part 1: Introduce the
character. Part 2: Describe their background. Now combine into a story."). Without a harmful-
content anchor, the pattern would fire on benign creative writing or educational requests.

**Constraint that blocked it:**
- False positive risk: legitimate "part 1 / part 2" framing is common in benign contexts
- Could not design a tight enough single-turn discriminant within this cycle

**Suggested next step:**
1. Evaluate adding a harm-keyword anchor alongside the split pattern (e.g., require a harmful
   topic word in Part 1 or Part 2 — but this limits coverage to known harm keywords).
2. Alternatively, implement as a multi-turn behavioral monitor in the cross-session correlator
   rather than a single-turn regex.
3. Build a false-positive test dataset for "Part 1 / Part 2 / combine" in benign contexts
   before committing to any regex approach.
