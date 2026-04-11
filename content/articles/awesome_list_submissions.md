# Awesome List Submissions – Aigis

---

## Submission 1: awesome-llm-security (or awesome-security)

**Target repo:** `corca-ai/awesome-llm-security` (primary); fallback: `sbilly/awesome-security`

**PR Title:** Add Aigis – open-source LLM prompt injection detection library

**PR Body:**

## Add Aigis to LLM Security Tools

Hi maintainers,

I'd like to add **Aigis** to the *LLM Security Libraries / Defensive Tools* section.

**Markdown line to add:**

```markdown
- [Aigis](https://github.com/killertcell428/aigis) - Open-source LLM security library. 53 detection patterns covering prompt injection, jailbreaks, PII leaks, and data exfiltration. OWASP LLM Top 10 coverage with remediation hints. 100% benchmark precision, zero dependencies.
```

**Why it belongs here:**

Aigis directly addresses the threats catalogued in this list – prompt injection (LLM01), sensitive information disclosure (LLM02), and jailbreaking (LLM04) – making it a natural fit alongside existing detection and mitigation tools. Unlike most alternatives, it provides CWE-classified findings and per-flag remediation hints, giving practitioners actionable output rather than a binary block signal. It is actively maintained, fully open-source (MIT), and installable with zero external dependencies via `pip install aigis`.

**Checklist:**
- [x] Link points to a public GitHub repository
- [x] Description is concise and follows list style
- [x] Not a duplicate of an existing entry
- [x] MIT licensed

---

## Submission 2: awesome-python-security

**Target repo:** `guardrails-ai/awesome-python-security` or `crypto-matto/awesome-python-security`

**PR Title:** Add Aigis – LLM prompt injection and jailbreak detection for Python apps

**PR Body:**

## Add Aigis to LLM / AI Application Security

Hi maintainers,

Proposing to add **Aigis** under the *AI / LLM Application Security* section (or *Input Validation & Sanitization* if no LLM-specific section exists yet).

**Markdown line to add:**

```markdown
- [Aigis](https://github.com/killertcell428/aigis) - Open-source LLM security library. 53 detection patterns covering prompt injection, jailbreaks, PII leaks, and data exfiltration. OWASP LLM Top 10 coverage with remediation hints. 100% benchmark precision, zero dependencies.
```

**Why it belongs here:**

LLM applications are rapidly becoming a standard Python deployment target, and prompt injection is now one of the most common attack vectors against Python-based AI services. Aigis fills a gap in this list by providing a Python-native, zero-dependency guardrail that integrates in three lines of code, making it accessible to developers who need security coverage without adding infrastructure overhead. The library exposes structured, CWE-tagged findings that integrate cleanly with existing Python logging and observability stacks.

**Checklist:**
- [x] Pure Python, no external runtime dependencies
- [x] pip-installable (`pip install aigis`)
- [x] Open-source (MIT)
- [x] Actively maintained

---

## Submission 3: awesome-llm / awesome-chatgpt-prompts (Security section)

**Target repo:** `f/awesome-chatgpt-prompts` (security/safety section) or `Hannibal046/Awesome-LLM`

**PR Title:** Add Aigis to Safety & Security – open-source guardrails with OWASP LLM Top 10 coverage

**PR Body:**

## Add Aigis to the Safety & Security Section

Hi maintainers,

I'd like to add **Aigis** to the *Safety, Security & Alignment / Guardrails* section of this list.

**Markdown line to add:**

```markdown
- [Aigis](https://github.com/killertcell428/aigis) - Open-source LLM security library. 53 detection patterns covering prompt injection, jailbreaks, PII leaks, and data exfiltration. OWASP LLM Top 10 coverage with remediation hints. 100% benchmark precision, zero dependencies.
```

**Why it belongs here:**

As LLM adoption grows, safety and security tooling has become a core concern for practitioners building on top of language models, and this list is a primary discovery resource for that audience. Aigis complements the alignment and safety papers already listed by offering a practical, deployable defensive layer – bridging the gap between research-level threat modeling and production-grade mitigation. Its explainability-first design (surfacing *why* a pattern was flagged, not just blocking it) aligns with the interpretability focus common in ML safety research referenced throughout this list.

**Checklist:**
- [x] Relevant to LLM safety and security practitioners
- [x] Open-source and freely available
- [x] Description follows list formatting conventions
- [x] Not a duplicate
