# Pending: Hardening Guide — AI Workflow Automation RCE (n8n, Langflow, LiteLLM)

**Title:** Hardening guide for AI workflow automation remote code execution class

**Motivation:**
Four CISA KEV-listed AI framework CVEs in Q1–Q2 2026 share the same root pattern: prompt
injection reaches an unsafe code execution default and escalates to host-level RCE within
hours of disclosure. A `docs/hardening/` guide would give operators a concrete checklist and
explain the shared attack pattern, making it easier to configure production deployments safely.

**Which research finding led to this idea:**
`auto-improvement/research/2026-05-18T00-07_9-incident-postmortems.md`
Candidate hardening #3 ("Hardening guide for AI framework file/image loader SSRF").

**Proposed Change:**
Create `docs/hardening/ai-workflow-rce.md` covering:
- The shared attack pattern: prompt injection → framework code execution default → host RCE
- Affected frameworks and CVEs: n8n (CVE-2026-21858, CVE-2026-27493), Langflow (CVE-2026-33017),
  LiteLLM (CVE-2026-42208), Semantic Kernel (CVE-2026-26030, CVE-2026-25592)
- Aigis rule coverage for each CVE: which rule detects which attack
- Operator checklist: patching cadence, CISA KEV monitoring, unsafe default audit

**Why it was held back:**
The two new patterns (`afe_n8n_expression_injection` and `sc_langchain_dangerous_code`)
consumed the non-test LOC budget for this cycle. Adding a 60+ LOC documentation file
would exceed the 100 LOC non-test limit.

**Which constraint blocked it:**
"Keep total non-test diff ≤ 100 LOC." The two pattern additions (~60 LOC non-test) plus a
guide would exceed the limit.

**Suggested Next Step for Human Reviewer:**
This is a documentation-only addition — no code changes to aigis itself. A future cycle
with fewer or smaller pattern additions can include it without hitting the LOC limit.
Alternatively, if the LOC limit for documentation-only additions can be relaxed, this
could be added in a standalone documentation cycle.
