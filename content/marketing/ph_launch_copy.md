# Product Hunt Launch Copy

## Launch Date: 2026-05-13 (Tuesday) 12:01 AM PT / 4:01 PM JST

---

## Tagline (60 chars max)
"Scan your AI agent's MCP tools for poisoning — zero dependencies"

## Alt Taglines
- "The first OSS security scanner for AI agents and MCP tools"
- "121 detection patterns for LLM security — zero dependencies"
- "Protect your AI agents from prompt injection in 3 lines of Python"

---

## Description (260 chars max)

Aigis scans LLM inputs, outputs, and MCP tool definitions for security threats. 121 detection patterns, 19 categories, 4 languages. Zero dependencies — just `pip install aigis`. The first and only open-source MCP security scanner.

---

## Maker Comment (First Comment — Post immediately after launch)

Hey Product Hunt! I'm the maker of Aigis.

**Why I built this:** I was using Claude Code with MCP tools and realized there's no way to verify if a tool definition is safe before the AI agent uses it. 43% of MCP servers have command injection vulnerabilities — and the tool descriptions go directly into the LLM's context window.

**What makes it different:**
- **First OSS MCP scanner** — 10 patterns covering 6 attack surfaces (poisoning, shadowing, rug pulls)
- **Zero dependencies** — Python stdlib only. No numpy, no transformers, no API calls
- **121 patterns / 19 categories** — prompt injection, jailbreak, PII (5 countries), memory poisoning, encoding bypass...
- **Auto red team** — `aig redteam` generates attacks to test your defenses
- **Multilingual** — EN, JA, KO, ZH natively

**Quick start:**
```
pip install aigis
aig scan "ignore previous instructions"
# → CRITICAL: Blocked
```

It's free, open-source (Apache 2.0), and I'm actively developing it. Would love your feedback on what attack vectors to add next!

GitHub: https://github.com/killertcell428/aigis

---

## Gallery Images Needed (5)

1. **Hero** — Logo + tagline + key stats (121 patterns, 19 categories, 0 dependencies)
2. **MCP Scanner Demo** — Terminal showing `aig mcp` detecting poisoned tool
3. **Detection Coverage** — Visual of 19 categories with pattern counts
4. **Integration** — Code snippet showing FastAPI/LangChain/Guard integration
5. **Benchmark** — 98/98 detection, 0% FP, ~1.6ms latency

---

## Topics/Tags
- Developer Tools
- Open Source
- Artificial Intelligence
- Cybersecurity
- Python

---

## Pre-Launch Checklist

### 4 weeks before (4/15)
- [ ] PH Draft created
- [ ] Maker profile complete (bio, photo, links)
- [ ] 20+ genuine comments on other products

### 3 weeks before (4/22)
- [ ] Gallery images ready (5 PNGs, 1270x760)
- [ ] Demo GIF/video (30-60 sec)
- [ ] 30+ comments, some Maker replies received

### 2 weeks before (4/29)
- [ ] Launch copy finalized
- [ ] 40+ comments
- [ ] 30 supporters notified via DM/email

### 1 week before (5/6)
- [ ] Go/NoGo decision
- [ ] 50 supporters confirmed
- [ ] All SNS posts pre-written
- [ ] Landing page optimized for PH → GitHub flow

### Launch day (5/13)
- [ ] Post at 12:01 AM PT
- [ ] Maker comment posted immediately
- [ ] X/Twitter thread posted at 12:05 AM PT
- [ ] Reddit posts at 6:00 AM PT
- [ ] Discord/Slack shares at 8:00 AM PT
- [ ] Zenn/Qiita記事 at 9:00 AM JST
- [ ] Respond to EVERY PH comment within 1 hour
