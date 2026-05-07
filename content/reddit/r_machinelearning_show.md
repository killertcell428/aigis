# r/MachineLearning — [P] Project submission

**Subreddit fit:** r/MachineLearning is academic-leaning. Posts must use `[P]` (project) tag and have technical substance. The 7-paper grounding is the hook — emphasize the research, not the product.

**Best window:** Tue–Thu 14:00–18:00 UTC. r/MachineLearning audience is global academic.

**Important:** mods are strict about self-promo. Lead with research, not "use my tool."

---

## Title

```
[P] Aigis: open-source reference implementation of 7 recent LLM-security papers (Mirror, StruQ, MI9, MemoryGraft, MSB, DataFilter, AdvJudge-Zero) as a single zero-dep Python library
```

## Body

**Background.** A lot of the 2025–2026 LLM-security literature publishes neat detection mechanisms but no usable code (or code that depends on a specific LLM API + 2GB of HF weights). I've spent the last few months porting 7 of these papers into a single zero-dependency Python library so they can actually be used and benchmarked side-by-side.

**The papers / mechanisms (each independently usable):**

| Paper | Mechanism in Aigis |
|---|---|
| Mirror Design Pattern (arxiv:2603.11875) | Input/output reflection asymmetry detector |
| StruQ + LLMail-Inject | Structured-prompt input/data separation guard |
| MI9 (arxiv:2508.03858) | Goal-conditioned FSM tracking runtime goal divergence |
| MemoryGraft (arxiv:2512.16962) | Long-term memory poisoning defence (graft detection at write & retrieval) |
| MSB (arxiv:2510.15994) | 3-stage MCP tool poisoning scanner |
| DataFilter + RAGDefender | RAG context filter (untrusted-content boundary marking) |
| AdvJudge-Zero | Judge-manipulation detection (LLM-as-judge attacks) |

**Why a single library, not 7 separate repos?**

1. **Comparable evaluation.** Same input format, same `CheckResult` schema → trivial to A/B detectors on your dataset.
2. **Composability.** The 4-wall + L4–L7 architecture lets you stack mechanisms (e.g., MI9 FSM + StruQ separation simultaneously) without writing glue code.
3. **Realistic deployment.** A research repo I can't actually drop in front of `chat()` is less useful than imperfect-but-deployable.

**What's open**

- Code: Apache-2.0, https://github.com/killertcell428/aigis
- 180+ patterns + 7 paper modules, all in plain Python (no `transformers`, no `spaCy` — stdlib only for the core engine)
- 940+ unit tests passing
- 44 compliance templates (US/CN/JP/EU regulatory FW)
- v1.0.0 released 2026-05-07

**What I want feedback on (the actual research questions)**

1. **MI9 goal-FSM coverage.** Paper defines 9 divergence states. I've implemented 7. Is the gap defensible, or am I missing something load-bearing?
2. **MemoryGraft retrieval-time check.** I do it both at write and retrieval. Paper does only write. Curious whether retrieval check actually helps in practice or just inflates latency.
3. **MSB false-positive rate on legitimate MCP tools.** Anyone running this against real-world MCP servers?

The README has a comparison table vs. LLM Guard / Guardrails AI / NeMo Guardrails on paper-coverage, MCP support, and self-improving loops, but I'd much rather hear from people who've actually run any of these in production.

---

## Posting checklist

- [ ] `[P]` tag in title (mandatory)
- [ ] Lead with the *research* angle, not the product
- [ ] Include the paper-table — mods like rigor
- [ ] Include limitations / open questions section
- [ ] Reply to first 2-3 comments within 1 hour to seed thread
