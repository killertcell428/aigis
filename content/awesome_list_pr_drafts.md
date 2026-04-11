# Awesome List PR Drafts

## 1. awesome-python (vinta/awesome-python)

**Section**: Security / Third-Party APIs
**PR Title**: Add Aigis — LLM security middleware
**Entry**:
```markdown
- [Aigis](https://github.com/killertcell428/aigis) - Zero-dependency middleware that detects prompt injection, jailbreaks, and data exfiltration in LLM applications. 64 regex-based patterns with 100% precision benchmark.
```

**Category candidates** (pick best fit):
- `Third-Party APIs > Security` (preferred — alongside other security-related tools)
- `Code Analysis > Security` (if security section is more relevant)

---

## 2. awesome-llm-security (corca-ai/awesome-llm-security)

**Section**: Defense Tools / Frameworks
**PR Title**: Add Aigis — open-source prompt injection detection library
**Entry**:
```markdown
### Defense Tools

- [Aigis](https://github.com/killertcell428/aigis) - Open-source Python library for protecting LLM applications. Features include:
  - 64 detection patterns (prompt injection, jailbreak roleplay, data exfiltration, PII, token exhaustion)
  - Zero dependencies (stdlib only)
  - FastAPI, LangChain, OpenAI, Anthropic, LangGraph middleware
  - Built-in benchmark: 53/53 attacks detected, 0% false positive
  - SaaS dashboard with Stripe billing (optional)
```

---

## 3. awesome-ai-safety (hari31416/awesome-ai-safety)

**Section**: Tools / Guardrails
**PR Title**: Add Aigis — LLM guardrails and security filter
**Entry**:
```markdown
- [Aigis](https://github.com/killertcell428/aigis) - Lightweight Python library for LLM security. Detects prompt injection, jailbreaks, PII leaks, and data exfiltration with 64 regex patterns. Zero dependencies, integrates with FastAPI/LangChain/OpenAI/Anthropic.
```

---

## PR Body Template (all 3 PRs)

```markdown
## What is this?

Aigis is an open-source Python library (`pip install aigis`) that protects LLM applications from prompt injection, jailbreaks, and data exfiltration attacks.

### Key features:
- **64 detection patterns** covering OWASP LLM Top 10 categories
- **Zero dependencies** (Python stdlib only)
- **100% precision** on built-in adversarial benchmark (53/53 attacks, 0/20 false positives)
- **One-line integration** with FastAPI, LangChain, OpenAI SDK, Anthropic SDK, and LangGraph
- **CLI tool** (`aig scan`, `aig benchmark`, `aig doctor`)
- **VS Code extension** for in-editor scanning

### Links:
- GitHub: https://github.com/killertcell428/aigis
- PyPI: https://pypi.org/project/aigis/
- Docs: https://aigis.vercel.app/docs/quickstart

Happy to adjust the entry text if needed!
```

---

## Submission Checklist

- [ ] Fork each repository
- [ ] Add entry in alphabetical order within the section
- [ ] Ensure description is concise (under 200 chars for awesome-python)
- [ ] Submit PR with the template body above
- [ ] Monitor for reviewer feedback
