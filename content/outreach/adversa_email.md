# Adversa AI — "Top Agentic AI security resources May 2026" inclusion email

**Target:** Adversa AI publishes a recurring "Top Agentic AI security resources" roundup. The May 2026 issue is the next slot.

**Recipient research checklist:**
- [ ] Visit https://adversa.ai/ → Blog/Resources to confirm the roundup is still active
- [ ] Find the author of the most recent issue (usually Alex Polyakov, founder, or a named researcher)
- [ ] Get their email from the post byline / LinkedIn / contact page
- [ ] If no email, message via LinkedIn DM with shorter version below

---

## Email — long version (for direct contact)

**Subject:** Aigis — open-source AI agent firewall implementing 7 of the papers you covered

Hi {{first name}},

I've been following Adversa's "Top Agentic AI security resources" roundup since the {{recent month}} issue and noticed several of the papers you've highlighted — Mirror, MI9, MemoryGraft, MSB — don't have practical open-source implementations that defenders can drop in front of an existing LLM app.

I just released **Aigis v1.0.0**, a zero-dependency Python firewall for AI agents that ports those exact papers (plus three more) into a single library. Wanted to flag it for the May 2026 roundup if it fits.

**One-paragraph summary**

Aigis is an Apache-2.0, zero-dependency Python firewall implementing 7 published 2025–2026 LLM-security papers — Mirror Design Pattern (arxiv:2603.11875), StruQ + LLMail-Inject, MI9 goal-conditioned FSM (arxiv:2508.03858), MemoryGraft defence (arxiv:2512.16962), MSB 3-stage MCP scanning (arxiv:2510.15994), DataFilter + RAGDefender, and AdvJudge-Zero. Each module is independently usable. 180+ patterns, 44 compliance templates (US/CN/JP/EU), and three deployment modes (library, Docker sidecar, CLI). 940+ tests passing.

**Why it might fit Adversa's roundup**

- **Practical implementation of papers you've already curated** — directly executable, not just citations
- **Agentic-first architecture** — 4 walls + L4 capability access control + L5 atomic execution + L6 safety verifier + L7 goal FSM, designed for tool-calling agents (Claude Code, Cursor, MCP)
- **Real deployment story** — drop-in for FastAPI / LangChain / OpenAI / Anthropic SDK; sidecar Docker image on GHCR
- **Independent / research-driven** — not a vendor product; no SaaS upsell

**Links**

- Repo: https://github.com/killertcell428/aigis
- v1.0.0 release: https://github.com/killertcell428/aigis/releases/tag/v1.0.0
- Comparison vs LLM Guard / Guardrails AI / NeMo Guardrails: in the README
- Docker quickstart: `docker run -p 8080:8080 ghcr.io/killertcell428/aigis`

I've also published technical writeups on three of the implemented papers (Zenn — Japanese audience, but the code in each post is universal):
- LiteLLM CVE-2026-42208 + sidecar guard pattern: https://zenn.dev/sharu389no/articles/20260502_litellm_cve42208
- Otter.ai post-meeting recording case study + privacy guard: https://zenn.dev/sharu389no/articles/aigis-v004-self-audit (linked)

Happy to send any additional material — benchmark numbers vs. specific attack corpora, integration walkthroughs for a particular framework, or written context on the design decisions for any of the seven modules.

Either way — your roundup has been one of the best filtered feeds for this space, thank you for the work.

Best,
{{name}}
{{role / handle}}
{{contact}}

---

## LinkedIn DM — short version (300-char limit)

Hi {{first name}}, just shipped Aigis v1.0.0 — zero-dep Python firewall for AI agents implementing 7 of the papers your "Top Agentic AI security resources" roundup has covered (Mirror, StruQ, MI9, MemoryGraft, MSB + 2 more). Apache-2.0, drop-in. Worth a flag for May? https://github.com/killertcell428/aigis

---

## Follow-up cadence

- Day 0: send email
- Day 7: if no response, post the same announcement publicly tagging Adversa's main account
- Day 14: do not chase further — move on

## What NOT to do

- ❌ Send to a generic `info@adversa.ai` — goes nowhere
- ❌ Pitch as "free SaaS demo" — Adversa is research-led, this would tank credibility
- ❌ Lead with the comparison table — lead with what's *new in the implementation* of papers they already know
