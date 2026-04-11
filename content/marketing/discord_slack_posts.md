# Discord / Slack Community Posts

## 1. OWASP Slack — #project-top10-for-llm

### Introduction Post
Hi everyone! I'm building an open-source LLM security library called Aigis (https://github.com/killertcell428/aigis).

It started as a prompt injection detector, but I've been expanding it to cover the OWASP LLM Top 10 more comprehensively. Currently at 121 detection patterns across 19 categories, including what I believe is the first OSS MCP tool poisoning scanner.

A few things I'd love to discuss with this community:
- **MCP security**: 43% of MCP servers have injection vulnerabilities. I've documented 6 attack surfaces — would love feedback on the taxonomy (https://github.com/killertcell428/aigis/blob/main/docs/compliance/MCP_SECURITY_ARCHITECTURE.md)
- **OWASP LLM Top 10 coverage**: I've mapped all patterns to the Top 10 — happy to share the matrix and get feedback on gaps
- **False positive rates**: Currently at 0% on our benchmark (98 attacks / 26 safe inputs). Always looking for more test cases.

The tool is zero-dependency (Python stdlib only), MIT licensed, and designed for easy integration with LangChain/FastAPI/OpenAI.

Happy to contribute detection patterns or test cases to any community projects here!

---

## 2. LangChain Discord — #showcase

### Post
Built a security middleware for LangChain apps — Aigis

It wraps your LLM calls with 121 detection patterns for prompt injection, jailbreak, PII, and more. Here's how it works:

```python
from aigis.middleware.langchain import AIGuardianCallback
from langchain_openai import ChatOpenAI

guard = Guard(policy="strict")
callback = AIGuardianCallback(guard=guard)
llm = ChatOpenAI(callbacks=[callback])

# Now every LLM call is automatically scanned
response = llm.invoke("user message here")
# If malicious → raises GuardianBlockedError
```

Also works with LangGraph via GuardNode for agent workflows.

New in v1.0: MCP tool definition scanning — if your agents use MCP tools, you can scan the tool definitions before the agent uses them.

Zero dependencies, ~1.6ms median latency per scan.

GitHub: https://github.com/killertcell428/aigis

---

## 3. Hugging Face Discord — #general or #discussion

### Post
Sharing an open-source LLM security project: Aigis

If you're deploying LLM apps, this adds a security layer that catches prompt injection, jailbreak, PII leakage, and 16 other threat types — with zero dependencies (no torch, no transformers needed).

What makes it different from other guardrails tools:
- First OSS MCP (Model Context Protocol) security scanner
- 121 regex + similarity patterns (no ML required, runs on CPU in ~1.6ms)
- Multilingual: EN, JA, KO, ZH
- Automated red teaming: `aig redteam` generates 9 categories of attacks

Interested in community feedback — especially on multilingual detection accuracy and new attack vectors you've seen.

https://github.com/killertcell428/aigis

---

## 4. MLOps Community Slack — #tools

### Post
Built an open-source security layer for LLM deployment pipelines: Aigis

Key for MLOps teams:
- `aig scan` in CI/CD to catch prompt injection in system prompts
- `aig benchmark` for automated security regression testing (98/98 attacks, 0% FP)
- `aig mcp` to audit MCP tool definitions before deployment
- `aig redteam` for pre-deployment adversarial testing
- `aig report` for compliance reports (OWASP LLM Top 10, NIST AI RMF)

Zero dependencies, integrates with FastAPI middleware for runtime protection.

https://github.com/killertcell428/aigis

---

## Posting Schedule
- Week 1 (4/14): OWASP Slack + LangChain Discord
- Week 2 (4/21): HuggingFace Discord + MLOps Slack
- Respond to all replies within 24 hours
- Don't cross-post the same day — space them out
