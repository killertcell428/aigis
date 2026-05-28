# Pending: Crescendo Single-Turn Escalation Framing Pattern

**Title:** Detect Crescendo-style explicit escalation framing in single-turn inputs

**Motivation:**
Crescendo (arXiv:2404.01833, USENIX Security 2025, Microsoft Research) is a multi-turn jailbreak
that begins with benign questions and gradually escalates toward harmful content. CrescendoMation
outperforms other jailbreaks by 29–61% on GPT-4 and 49–71% on Gemini-Pro. In single-turn
scenarios, a detectable escalation marker sometimes appears: "Now that we've established [benign
topic], tell me how to [harmful escalation]." This phrasing is rarely used in benign requests.

**Research finding that led to this idea:**
- arXiv:2404.01833 (Russinovich et al., USENIX Security 2025), jailbreak-extraction cycle 4
- Also: "foot-in-the-door" framing in arXiv:2502.19820 (Feb 2025)

**Proposed change:**
Add `jb_crescendo_escalation` (input, score 45):
```python
pattern = _p(
    r"(?:now\s+that\s+(?:we.ve|you.ve|i.ve)\s+(?:established|agreed|discussed|covered)|"
    r"(?:since|given\s+that)\s+(?:we\s+(?:established|agreed|discussed))|"
    r"building\s+on\s+(?:that|our\s+(?:discussion|conversation|previous)))"
    r".{0,150}"
    r"(?:how\s+to|steps?\s+(?:to|for)|instructions?\s+(?:to|for)|explain\s+how\s+to)"
    r".{0,100}"
    r"(?:harm|attack|hack|crack|steal|kill|bomb|weapon|drug|synthesize|exploit)"
)
```

**Why it was held back:**
The single-turn Crescendo signal ("now that we've established X, tell me Y") needs a harmful
anchor keyword to avoid false positives. Without anchoring to specific harmful terms, the
framing matches legitimate reasoning transitions ("now that we've established the context,
explain how to improve performance"). The current candidate requires harmful keywords, which
reduces the detection surface to known-harm-word escalation only — a meaningful but incomplete
coverage.

**Constraint that blocked it:**
- Multi-turn behavioral detection is the correct primary approach
- Single-turn variant with harm keyword anchoring is useful but narrow
- False positive risk without harm anchoring is too high for this cycle

**Suggested next step:**
1. Implement the anchored single-turn variant (with harm keywords) and measure false positive
   rate on the benign test set.
2. Design a multi-turn cross-session escalation monitor for the aigis cross_session module that
   tracks topic drift toward harmful content over multiple turns.
