# r/netsec — Show submission

**Subreddit rules to check:** r/netsec uses a "Showcase Saturday" thread on weekends for self-promo. Outside of that, posts must be of genuine technical interest (not marketing). Best window: Saturday, post a comment thread with code/findings.

**Type:** Link post (to GitHub) with explanatory body, OR Showcase Saturday top-level comment.

---

## Title (under 300 chars; r/netsec prefers descriptive)

```
Aigis v1.0.0: zero-dep Python firewall for AI agents — 7 published papers (Mirror, StruQ, MI9, MemoryGraft, MSB, DataFilter, AdvJudge-Zero) implemented as a 3-line drop-in
```

## URL

`https://github.com/killertcell428/aigis`

## Body

I've been working on **Aigis**, an Apache-2.0 Python firewall for LLM apps and AI agents, and just shipped v1.0.0. Posting here because the design choices may be of interest to people who've looked at LLM Guard, NeMo Guardrails, or rolled their own filters.

**What's in v1.0.0**

- **180+ detection patterns** across OWASP LLM Top 10 (prompt injection, jailbreak, PII, exfiltration, system-prompt extraction, judge manipulation), each tagged with `owasp_ref` + `remediation_hint`
- **7 published papers as separately-usable modules**, each zero-dependency:
  - Mirror Design Pattern (arxiv:2603.11875) — input/output reflection asymmetry
  - StruQ + LLMail-Inject — structured-prompt input/data separation
  - MI9 goal-conditioned FSM (arxiv:2508.03858) — runtime goal divergence detection
  - MemoryGraft (arxiv:2512.16962) — long-term memory poisoning defence
  - MSB (arxiv:2510.15994) — 3-stage MCP tool poisoning scanner
  - DataFilter + RAGDefender — RAG context filtering
  - AdvJudge-Zero — judge-manipulation detection
- **44 compliance templates** across US (NIST AI RMF, EU AI Act), CN (生成式AI管理弁法), JP (AI事業者ガイドライン), EU (AI Act, GDPR)
- **Three deployment modes** with the same engine: Python library, Docker sidecar (`docker run ghcr.io/killertcell428/aigis`), or CLI

**Why I built it**

Existing OSS guard libraries are either heavyweight (NeMo, LLM Guard pull in transformers + spaCy + half of HF) or single-purpose (Rebuff for PI only, Garak for offline scanning). Drop-in for an existing Claude Code / Cursor / FastAPI app needed something different:

- *Zero-dependency core* — the entire Guard works on Python stdlib. ML models are optional plugins.
- *Paper-grounded* — each detector cites a 2025–2026 paper or disclosure
- *Three lines of integration*:
  ```python
  from aigis import Guard
  result = Guard().check_input(user_text)
  if result.blocked: ...
  ```

**What I'd love feedback on**

1. **False-positive rate.** 940+ tests pass internally but synthetic data ≠ production. Anyone who's running it in front of real LLM traffic, please open issues.
2. **MCP scanning coverage.** MSB-based but I'm not deeply involved in the MCP ecosystem. If your team uses MCP, the Aigis MCP scanner would benefit from real-world tool descriptions.
3. **The right comparison set.** Is there a tool I should benchmark against beyond LLM Guard, Guardrails AI, NeMo, Rebuff?

Repo (with full README, comparison table, papers list): https://github.com/killertcell428/aigis
v1.0.0 release notes: https://github.com/killertcell428/aigis/releases/tag/v1.0.0

Apache-2.0, no telemetry, no SaaS upsell.

---

## Posting checklist

- [ ] Wait for Showcase Saturday thread, OR post weekday with strong technical hook
- [ ] No "please star my repo" language
- [ ] First comment from author = TL;DR + reply to expected mod question (why post here, not r/MachineLearning)
- [ ] Cross-link from HN Show HN if both are live
