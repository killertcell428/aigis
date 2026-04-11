# Aigis — Product Hunt Launch Copy

## Product Name
Aigis

## Tagline (60 chars max)
The open-source firewall for AI agents

## Description (260 chars max)
Block prompt injections, jailbreaks, and data leaks before they reach your LLM. 4-layer defense, MCP tool security, US/CN/JP/EU compliance templates. One line of code. Zero dependencies. Free forever. Built for the agent era.

## Full Description (Maker Comment)

Hey Product Hunt!

I built Aigis because every AI security tool I found was either:
- $50K+/year enterprise software, or
- A single-layer scanner that misses obfuscated attacks

Aigis is different:

**What it does:**
Your AI agents call tools, read files, and make decisions autonomously. One prompt injection can hijack all of that. Aigis sits between user input and your LLM, blocking attacks before they ever execute.

**Why it's different from existing tools:**

1. **4 independent defense layers** — not just regex. Similarity matching catches paraphrased attacks. Encoded payload detection catches Base64/hex obfuscation. Multi-turn analysis catches slow-burn attacks across conversation turns.

2. **Built for the agent era** — MCP tool poisoning detection (43% of MCP servers have vulnerabilities), capability-based access control, supply chain hash pinning. Most tools were built for chatbots. Aigis was built for agents.

3. **44 compliance templates across 4 countries** — US (OWASP, NIST, SOC2, HIPAA, PCI-DSS), China (GenAI Measures, PIPL), Japan (AI Business Guidelines, APPI), EU (GDPR). Pick what your industry needs, skip what you don't.

4. **Self-improving** — Run `aigis adversarial-loop` and it attacks itself, finds gaps, and writes new detection rules. Your defense gets stronger every cycle.

**Quick start:**
```
pip install pyaigis

from aigis import Guard
guard = Guard()
result = guard.check_input(user_message)
if result.blocked:
    return "Nice try."
```

Zero dependencies. Works with OpenAI, Anthropic, LangChain, FastAPI, or any Python app.

**What's included (all free, Apache 2.0):**
- CLI: `aigis scan`, `aigis redteam`, `aigis monitor`
- SDK: Python library with middleware for FastAPI/LangChain/OpenAI/Anthropic
- Dashboard: Web UI with monitoring, policy editor, audit logs, compliance reports
- 901 tests passing, 98.9% detection rate

Named after the Aegis — the shield of Zeus. AI + Aegis = Aigis.

Would love your feedback!

## Topics / Tags
- Artificial Intelligence
- Open Source
- Developer Tools
- Cybersecurity
- Privacy

## Gallery Images (5 needed)

### Image 1: Hero
- Title: "The open-source firewall for AI agents"
- Show: Stat block (98.9% detection, 901 tests, 44 templates, $0)
- Background: Dark theme matching the dashboard

### Image 2: 4-Layer Defense
- Title: "4 walls between attackers and your LLM"
- Show: The ASCII pipeline diagram from README, visualized as 4 colored walls
- Caption: "Most tools have 1 layer. Aigis has 4."

### Image 3: Dashboard
- Title: "Security monitoring built in"
- Show: Screenshot of /monitoring page (ASR trend, OWASP scorecard, risk distribution)

### Image 4: Policy Templates
- Title: "44 compliance templates. Pick what you need."
- Show: Screenshot of policy page with grouped templates (JP/US/CN/EU flags)

### Image 5: Playground Demo
- Title: "Try to break it"
- Show: Screenshot of playground with SQL injection blocked

## Launch Checklist
- [ ] Product Hunt Draft created
- [ ] 5 gallery images prepared (1200x800 or 1270x760)
- [ ] OG image (1200x630)
- [ ] Demo video (optional, 2 min max)
- [ ] First comment (maker comment) ready
- [ ] 3+ hunter/supporter accounts notified
- [ ] Social media posts scheduled (Twitter, LinkedIn, Reddit)
- [ ] Launch time: 12:01 AM PT (Wednesday recommended)
