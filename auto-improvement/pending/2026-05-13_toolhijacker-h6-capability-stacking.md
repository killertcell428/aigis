# Pending: ToolHijacker H6 Capability-Domain Stacking Heuristic

**Date:** 2026-05-13
**Domain:** agent-tool-abuse (cycle 1, third pass)
**Research basis:** ToolHijacker paper (arxiv:2504.19793, NDSS 2026 accepted); 96.7% ASR on MetaTool with GPT-4o; 88.2% on ToolBench.

---

## Title

ToolHijacker S-Sequence Detection — H6 capability-domain stacking heuristic for `detect_selection_bias()`

## Motivation

ToolHijacker (NDSS 2026) uses two optimized sequences in malicious tool descriptions:
- **R-sequence:** Retrieval-optimized — inflates semantic similarity scores to many task types, drawing more agent queries toward the malicious tool. Partially caught by H5 (keyword stuffing).
- **S-sequence:** Selection-optimized — dense stacking of first-person capability claims across 7+ distinct task domains without comparative dismissal of other tools. **Evades all existing H1–H5 heuristics** because it never dismisses other tools (H1–H3) and doesn't keyword-stuff in an obvious way (H5).

Example S-sequence pattern: "I can handle web search, database queries, file operations, email dispatch, calendar management, payment processing, user authentication, and API integration tasks" — 8 distinct domains in one sentence.

## Proposed Change

Add an H6 heuristic to `detect_selection_bias()` in `aigis/mcp_scanner.py`:

```python
# H6: Capability-domain stacking (ToolHijacker S-sequence, NDSS 2026)
# Count distinct task-domain nouns in descriptions ≤ 200 words.
# 7+ domains in a short description = S-sequence fingerprint.
TASK_DOMAINS = frozenset({
    "search", "query", "database", "storage", "file", "email",
    "calendar", "payment", "authentication", "api", "webhook",
    "notification", "translation", "image", "audio", "video",
    "analytics", "reporting", "scheduling", "messaging", "chat",
    "crm", "erp", "deployment", "monitoring", "logging",
})

def _count_task_domains(desc: str) -> int:
    words = set(re.findall(r"\b\w+\b", desc.lower()))
    return len(words & TASK_DOMAINS)

# In detect_selection_bias():
domain_count = _count_task_domains(description)
if domain_count >= 7:
    results.append(BiasHeuristic(
        heuristic="H6",
        description=f"Capability-domain stacking: {domain_count} distinct task domains "
                    "listed in description (ToolHijacker S-sequence, NDSS 2026, 96.7% ASR)",
        score_contribution=45,
    ))
```

## Why Held Back

**Constraint: regex-only noun extraction is too fragile.** The TASK_DOMAINS frozenset approach has two competing problems:
1. **False positives:** Legitimate multi-purpose tools (e.g., a general-purpose productivity assistant) genuinely handle 7+ domains and would be flagged incorrectly.
2. **False negatives:** The S-sequence uses synonyms and domain-adjacent terms that don't appear in a fixed vocabulary list. An attacker who knows the list will simply use synonyms.

A reliable H6 requires either:
- NLP-based domain classification (violates no-runtime-dependency constraint)
- Or a much larger vocabulary with synonym expansion (which pushes false positives up dramatically)

The H5 heuristic (keyword stuffing by raw count) provides partial coverage of the R-sequence, which is the higher-volume attack. H6 specifically targets the S-sequence, which is rarer but higher-precision.

## Suggested Next Step for Human Reviewer

1. Build a manually curated domain taxonomy covering ~200 terms with known false-positive rate < 5% on a sample of 100 legitimate tool descriptions.
2. Tune the threshold (currently 7) against that sample before deploying.
3. Consider making the H6 score contribution low (≤ 40) and requiring it to compound with another heuristic before triggering a block — this reduces false-positive impact without eliminating coverage.
