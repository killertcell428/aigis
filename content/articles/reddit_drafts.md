# Reddit Drafts – Aigis (aigis)

---

## Post 1: r/Python

**Title:** I built an open-source Python library to protect LLM apps from prompt injection – Show r/Python

**Body:**

Hey r/Python! I just released `aigis`, a zero-dependency Python library for protecting LLM-powered apps from prompt injection, PII leaks, and jailbreak attempts.

Getting started takes literally 3 lines:

```python
from aigis import Guard

guard = Guard()
result = guard.check_input(user_input)

if result.blocked:
    print(result.reasons[0])   # tells you *why*, not just that it failed
    print(result.remediation)  # concrete fix suggestion
```

Key points for Pythonistas:

- **Zero external dependencies** – pure stdlib, no bloat
- **pip install aigis** and you're done
- Covers **53 attack patterns** including indirect injection and multi-turn attacks
- 100% precision on built-in adversarial benchmark (53/53 attacks detected, 0% false positive rate)
- Each flag comes with a human-readable reason and a remediation hint so you know what to fix, not just what broke
- Works with any LLM backend: OpenAI, Anthropic, local models – doesn't matter

I built this because every guardrail library I tried either required a cloud call or just returned `True/False` with no explanation. Feedback and PRs very welcome!

- GitHub: https://github.com/killertcell428/aigis
- PyPI: `pip install aigis`

---

## Post 2: r/netsec → ❌ 動画投稿のみ受付。代替: r/cybersecurity / r/AskNetsec / r/hacking

**Title:** Aigis: Open-source LLM security scanner with OWASP LLM Top 10 coverage and remediation hints

**Body:**

Sharing a project I've been working on: **Aigis** (`aigis`), an open-source security library for LLM applications.

**Coverage:**

- **53 detection patterns** spanning OWASP LLM Top 10 categories (LLM01 through LLM10)
- Built-in benchmark: `aig benchmark` — 100% precision on 53 adversarial test cases, 0% false-positive rate on 20 benign inputs
- CWE classification on every finding so results map directly into your existing vuln tracking workflow
- Detects prompt injection, indirect injection via retrieved context, PII exfiltration attempts, jailbreak scaffolding, and role-confusion attacks

**What makes it different from a simple regex filter:**

- Semantic similarity layer catches paraphrased variants that evade keyword lists
- Multi-turn context tracking flags attacks that span multiple conversation turns
- Remediation hints tell you not just what was flagged but how to harden the prompt or pipeline

**What I need from this community:**

I'm actively collecting bypass samples and edge cases. If you're doing LLM red-teaming and hit a pattern that slips through, please open an issue or drop it in the repo discussions. The detection corpus grows with community input.

- GitHub: https://github.com/killertcell428/aigis
- PyPI: `pip install aigis`

---

## Post 3: r/MachineLearning → ❌ 認証済みユーザーのみ。代替: r/artificial / r/LocalLLaMA / r/LLMDevs / r/ChatGPTCoding

**Title:** Show r/ML: Open-source guardrails library for LLM apps – focuses on WHY something was flagged, not just blocking

**Body:**

Hi r/ML – sharing **Aigis**, an open-source guardrails library I built with a focus on explainability rather than just binary pass/fail blocking.

**Technical architecture highlights:**

- **53 regex patterns + semantic similarity layer** – regex covers known attack signatures (100% precision, 0% false positive); semantic matching catches paraphrased injection attempts that pure regex misses; configurable cosine similarity threshold per threat class
- **RAG context scanning** – scans retrieved documents before they are injected into the prompt, flagging indirect injection payloads embedded in external content
- **Multi-turn attack detection** – maintains a lightweight conversation state to detect attacks that distribute malicious intent across multiple turns (a common bypass for stateless scanners)
- **Structured output per finding** – every flagged item returns threat class, CWE ID, confidence score, matched evidence span, and a remediation hint, making it composable with logging and eval pipelines

The reasoning behind prioritizing explainability: when a guardrail silently blocks a request in production, engineers have no signal to improve prompts or pipeline design. Surfacing *why* a pattern was flagged closes that feedback loop.

Happy to discuss the detection design or threat modeling approach in the comments.

- GitHub: https://github.com/killertcell428/aigis
- PyPI: `pip install aigis`
