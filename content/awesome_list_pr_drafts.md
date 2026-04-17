# Awesome List PR Drafts

> **Last refreshed: 2026-04-18 (after v0.0.4 release).**
> Numbers updated: 180+ patterns (incl. new `judge_manipulation`), 940+ tests, zero deps.
> PyPI package name is `pyaigis` (not `aigis`). Keep entries under 200 chars where the list requires.

## 1. awesome-python (vinta/awesome-python)

**Section**: Security / Third-Party APIs
**PR Title**: Add Aigis — LLM security middleware
**Entry** (under 200 chars):
```markdown
- [Aigis](https://github.com/killertcell428/aigis) - Zero-dependency Python firewall for AI agents: 180+ patterns across OWASP LLM Top 10, MCP security, RAG context filtering, agent-FSM conformance.
```

**Category candidates**:
- `Third-Party APIs > Security` (preferred)
- `Code Analysis > Security`

---

## 2. awesome-llm-security (corca-ai/awesome-llm-security)

**Section**: Defense Tools / Frameworks
**PR Title**: Add Aigis — open-source prompt injection detection library with 2025–2026 research coverage
**Entry**:
```markdown
### Defense Tools

- [Aigis](https://github.com/killertcell428/aigis) - Zero-dependency Python library for LLM and agent security. Features:
  - **180+ detection patterns** (prompt injection, jailbreak, PII, data exfil, `judge_manipulation` for LLM-as-Judge attacks, and more)
  - **Recent research, implemented**: Mirror Design Pattern (2026), StruQ, MI9 goal-conditioned FSM, MemoryGraft defence, MSB 3-stage MCP scanning, DataFilter / RAGDefender for RAG context filtering, AdvJudge-Zero defence
  - **Zero dependencies** (stdlib only)
  - **FastAPI / LangChain / LangGraph / OpenAI / Anthropic / MCP** middleware
  - **Multi-layer defence**: 4 walls (regex, similarity, encoded payloads, multi-turn) + L4 capability ACC + L5 atomic execution pipeline + L6 safety verifier + L7 goal FSM
  - 940+ tests passing, public self-audit in CHANGELOG
```

---

## 3. awesome-ai-safety (hari31416/awesome-ai-safety)

**Section**: Tools / Guardrails
**PR Title**: Add Aigis — LLM guardrails and agent security library
**Entry** (under 200 chars):
```markdown
- [Aigis](https://github.com/killertcell428/aigis) - Zero-dep Python library for LLM and agent safety. 180+ patterns, MCP scanning, RAG context filter, goal-conditioned FSM. Integrates with FastAPI/LangChain/OpenAI/Anthropic.
```

---

## 4. awesome-mcp (candidate: punkpeye/awesome-mcp-servers or similar)

**Section**: MCP security / tooling
**PR Title**: Add Aigis — MCP security scanner (3-stage coverage)
**Entry**:
```markdown
- [Aigis MCP scanner](https://github.com/killertcell428/aigis) - Scans MCP servers for tool poisoning, rug pull, cross-tool shadowing; v0.0.4 adds runtime invocation/response scanning following the MSB 3-stage classification (arxiv:2510.15994). Zero Python deps.
```

*(Only submit if such a list exists and is accepting PRs — skip otherwise.)*

---

## PR Body Template (all PRs)

```markdown
## What is this?

Aigis (`pip install pyaigis`) is an open-source Python firewall for AI agents and LLM applications. Zero-dependency core, Apache 2.0.

### Key points for this list

- **180+ detection patterns** across OWASP LLM Top 10, with per-pattern `owasp_ref` + `remediation_hint` metadata
- **Recent 2025–2026 research implemented as modules**: Mirror Design Pattern (fast_screen), StruQ + LLMail-Inject (structured_query), MI9 (goal-conditioned FSM), MemoryGraft (memory imitation detector), MSB (MCP 3-stage scanning), DataFilter + RAGDefender (RAG context filter), AdvJudge-Zero (judge_manipulation patterns)
- **One-line middleware** for FastAPI, LangChain, LangGraph, OpenAI, Anthropic, MCP
- **940+ tests passing**, public self-audit findings in [v0.0.4 CHANGELOG](https://github.com/killertcell428/aigis/releases/tag/v0.0.4)

### Links
- GitHub: https://github.com/killertcell428/aigis
- PyPI: https://pypi.org/project/pyaigis/
- Docs: https://github.com/killertcell428/aigis/tree/master/docs

Happy to trim / rewrite the entry to match the list's conventions — let me know.
```

---

## Submission Checklist

- [ ] Fork each repository
- [ ] Add entry in alphabetical order within the section
- [ ] Ensure description is concise (under 200 chars for awesome-python)
- [ ] Submit PR with the template body above
- [ ] Monitor for reviewer feedback
