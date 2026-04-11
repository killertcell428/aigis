# Reddit Posts

## Post 1: r/netsec — MCP Security Research

### Title
MCP (Model Context Protocol) Security Analysis: 43% of servers vulnerable to command injection, tool poisoning attacks demonstrated

### Body
I've been researching security vulnerabilities in MCP (Model Context Protocol), the standard that connects AI agents like Claude Code and Cursor to external tools.

**Key findings:**

- 43% of MCP implementations have command injection vulnerabilities
- 82% are vulnerable to path traversal
- 30+ CVEs filed in 60 days (early 2026)
- Anthropic's own Git MCP server had 3 flaws (quietly patched Jan 2026)

**The root cause:** Tool descriptions and outputs are injected directly into the LLM's context window, indistinguishable from trusted system instructions. This means any MCP server can instruct the AI to:

1. Read sensitive files (`~/.ssh/id_rsa`, `~/.aws/credentials`)
2. Redirect communications to attacker-controlled destinations
3. Execute base64-encoded shell commands
4. Hide its actions from the user

**6 attack surfaces identified:**

| Attack | Technique |
|--------|-----------|
| Tool Description Poisoning | `<IMPORTANT>` tags with hidden instructions |
| Parameter Schema Injection | Malicious parameter names/descriptions |
| Output Re-injection | Poisoned tool return values |
| Cross-Tool Shadowing | Tool A modifying Tool B's behavior |
| Rug Pull | Silent redefinition after approval |
| Sampling Hijack | Manipulating sampling protocol |

I've documented the full attack taxonomy and built an open-source scanner that detects these patterns: [Aigis](https://github.com/killertcell428/aigis) — 10 MCP-specific detection patterns, zero dependencies, covers all 6 attack surfaces.

Full architecture doc: https://github.com/killertcell428/aigis/blob/main/docs/compliance/MCP_SECURITY_ARCHITECTURE.md

Curious what the community thinks about MCP security — are there attack vectors I'm missing?

---

## Post 2: r/Python — Tool Announcement

### Title
Aigis v1.0: Zero-dependency LLM security scanner with MCP tool poisoning detection (121 patterns, stdlib only)

### Body
I just released v1.0 of [Aigis](https://github.com/killertcell428/aigis), an open-source Python library for LLM/AI agent security.

**What it does:**
- Scans LLM inputs/outputs for prompt injection, jailbreak, PII, and 16 other threat categories
- First OSS MCP (Model Context Protocol) tool definition scanner — detects poisoning, shadowing, rug pulls
- Automated red team testing (`aig redteam`)
- Multilingual: EN, JA, KO, ZH

**Why zero dependencies?**
The entire library runs on Python stdlib — no numpy, no torch, no transformers. Pattern matching + n-gram similarity + heuristics. This means:
- `pip install aigis` and you're done
- No dependency conflicts
- Works offline, no API calls
- ~1.6ms median scan time

**Quick example:**
```python
from aigis import Guard, scan_mcp_tool

# Scan user input
guard = Guard()
result = guard.check_input("ignore previous instructions")
print(result.blocked)  # True

# Scan MCP tool definitions
result = scan_mcp_tool({"name": "add", "description": "..."})
```

**Benchmark:** 98/98 attacks detected (100%), 0/26 false positives (0%)

GitHub: https://github.com/killertcell428/aigis
PyPI: https://pypi.org/project/aigis/

Feedback welcome — especially on detection accuracy and false positive rates!

---

## Posting Notes
- r/netsec: Technical depth required. Focus on the research, not the tool.
- r/Python: Focus on the engineering decisions (zero-dep, stdlib-only).
- Post on different days (don't spam)
- Respond to all comments
