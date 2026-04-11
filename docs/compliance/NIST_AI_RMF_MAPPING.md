# Aigis — NIST AI Risk Management Framework (AI RMF 1.0) Alignment

> Last updated: 2026-04-10
> Aigis version: v1.3.1
> Reference: [NIST AI RMF 1.0](https://www.nist.gov/itl/ai-risk-management-framework)

## Overview

Aigis aligns with the NIST AI Risk Management Framework across all four core functions. This document maps Aigis's capabilities to the framework's subcategories, demonstrating how the product supports organizations in managing AI risks.

## Alignment Summary

| Function | Subcategories | Aigis Support Level |
|----------|:------------:|:-------------------------:|
| **GOVERN** | 6 | Supports |
| **MAP** | 5 | Supports |
| **MEASURE** | 4 | **Direct** |
| **MANAGE** | 4 | **Direct** |

---

## GOVERN — Policies, processes, and organizational structures

Aigis supports the Govern function through its policy engine and configuration framework.

| Subcategory | Description | Aigis Capability |
|-------------|-------------|----------------------|
| **GV-1** | Policies for AI risk management are defined | YAML policy engine allows organizations to define custom detection rules, risk thresholds, and response actions per deployment |
| **GV-2** | Roles and responsibilities are established | Middleware integration (FastAPI, LangChain) enables security team ownership of AI guardrails separate from development teams |
| **GV-3** | Organizational AI risk tolerance is defined | Configurable risk levels (LOW/MEDIUM/HIGH/CRITICAL) with per-policy thresholds. Organizations define what score triggers block/review/allow |
| **GV-4** | Risk management is integrated into broader enterprise processes | API-first design enables integration with existing SIEM, logging, and incident response workflows |
| **GV-5** | Processes for engagement with external stakeholders | Open-source core enables transparency and external audit. Benchmark suite provides reproducible risk assessment |
| **GV-6** | Policies address AI system lifecycle | Supports dev/staging/production with environment-specific policies. CI/CD integration via CLI (`aig scan`, `aig benchmark`) |

### How Aigis helps:
```yaml
# Example: Organization-specific risk policy
policy:
  name: "enterprise-strict"
  risk_threshold: 30  # Block anything above LOW
  custom_rules:
    - pattern: "confidential|internal only"
      score: 60
      category: "data_classification"
  actions:
    high: block
    medium: review
    low: allow
```

---

## MAP — Categorize and identify AI risks

Aigis supports the Map function by providing comprehensive threat categorization aligned with industry-standard taxonomies.

| Subcategory | Description | Aigis Capability |
|-------------|-------------|----------------------|
| **MP-1** | Context is established for AI system risk | 11 threat categories covering the full attack surface: prompt injection, jailbreak, SQL injection, data exfiltration, command injection, PII input, confidential data, token exhaustion, prompt leak, indirect injection, harmful content |
| **MP-2** | AI risks are categorized | Each detection pattern includes OWASP LLM Top 10 and CWE references. Risk scoring with category-level aggregation and diminishing returns |
| **MP-3** | AI system benefits and costs are assessed | Benchmark suite quantifies detection accuracy (precision/recall) and false positive rates per category. Zero-dependency design minimizes operational cost |
| **MP-4** | Risks related to third-party AI are addressed | `scan_rag_context()` API scans external content (RAG, web scraping) before insertion into prompts. Indirect injection patterns detect third-party content manipulation |
| **MP-5** | AI impacts are characterized | Remediation hints on every matched pattern provide actionable guidance. OWASP/CWE references enable standard impact classification |

### Threat category mapping:
```
Aigis Category        → NIST AI RMF Risk Domain
─────────────────────────────────────────────────────
prompt_injection            → Security & Resilience
jailbreak                   → Security & Resilience
sql_injection               → Security & Resilience
data_exfiltration           → Privacy & Security
command_injection           → Security & Resilience
pii_input                   → Privacy
confidential                → Privacy & Security
token_exhaustion            → Reliability & Resilience
prompt_leak                 → Security (IP Protection)
indirect_injection          → Security & Resilience
harmful_content (output)    → Safety & Fairness
pii_leak (output)           → Privacy
secret_leak (output)        → Security
```

---

## MEASURE — Analyze, assess, and monitor AI risks

Aigis directly implements the Measure function through its detection engine and benchmark framework.

| Subcategory | Description | Aigis Capability |
|-------------|-------------|----------------------|
| **MS-1** | AI risks and benefits are monitored | Real-time input/output scanning with risk scoring (0-100). `check_input()` and `check_output()` return structured `CheckResult` with risk level, matched rules, and remediation |
| **MS-2** | AI systems are evaluated for trustworthiness | Built-in adversarial benchmark suite: 79 attack vectors across 12 categories, 26 safe inputs. `aig benchmark` CLI command for reproducible evaluation |
| **MS-3** | AI risk tracking mechanisms are in place | Structured `MatchedRule` output includes pattern ID, category, score, description, and OWASP reference. Integrates with logging/SIEM for audit trails |
| **MS-4** | Feedback from affected communities is gathered | Open-source community contributions via GitHub Issues and Discussions. Pattern updates driven by real-world attack research |

### Measurement capabilities:
```python
from aigis import Guard

guard = Guard(policy="strict")
result = guard.check_input("user input here")

# Structured risk assessment
print(result.risk_score)      # 0-100
print(result.risk_level)      # LOW / MEDIUM / HIGH / CRITICAL
print(result.matched_rules)   # List of MatchedRule with OWASP refs
print(result.remediation)     # Actionable guidance
print(result.blocked)         # Policy decision
```

### Benchmark output:
```bash
$ aig benchmark --json
{
  "overall_precision": 100.0,
  "false_positive_rate": 0.0,
  "categories": [
    {"category": "prompt_injection", "precision": 100.0},
    {"category": "jailbreak", "precision": 100.0},
    ...
  ]
}
```

---

## MANAGE — Prioritize, respond to, and communicate AI risks

Aigis directly implements the Manage function through its policy engine, remediation system, and integration framework.

| Subcategory | Description | Aigis Capability |
|-------------|-------------|----------------------|
| **MN-1** | AI risks are prioritized | Category-aware scoring with configurable thresholds. Diminishing returns scoring prevents category stacking. Risk levels (LOW ≤30, MEDIUM 31-60, HIGH 61-80, CRITICAL >80) |
| **MN-2** | AI risks are responded to | Policy actions: `block` (reject input), `review` (flag for human review), `allow` (pass through). Middleware integration for automatic enforcement |
| **MN-3** | AI risk management is communicated | Every detection includes human-readable description, OWASP/CWE reference, and remediation hint. Supports JSON output for dashboards and reports |
| **MN-4** | AI risk treatments are documented | Full audit trail: pattern ID, input text (redactable), timestamp, risk score, policy decision. YAML policy files serve as documented risk treatment plans |

### Risk response flow:
```
User Input → Normalize → Pattern Match → Score → Policy Evaluate → Action
                                                          │
                                          ┌───────────────┼───────────────┐
                                          ▼               ▼               ▼
                                        BLOCK           REVIEW          ALLOW
                                     (reject +       (flag for        (pass +
                                      log +          human +           log)
                                      remediate)      queue)
```

### Integration points for risk management:
- **FastAPI middleware**: Automatic request/response scanning
- **LangChain integration**: `AIGuardianChain` wrapper
- **LangGraph**: `GuardNode` for agent workflow protection
- **CLI**: `aig scan` for CI/CD pipeline integration
- **Python API**: Direct integration in any Python application

---

## NIST AI RMF Playbook Alignment

The following table maps specific NIST AI RMF Playbook actions to Aigis features:

| Playbook Action | Aigis Feature |
|----------------|-------------------|
| Conduct AI impact assessments | `BenchmarkSuite.run()` — automated adversarial testing |
| Implement technical controls for AI risks | 83 detection patterns across 11 categories |
| Monitor AI system behavior | Real-time input/output scanning with structured logging |
| Establish AI incident response procedures | Policy-based block/review/allow with remediation hints |
| Document AI risk management activities | YAML policies + JSON audit output + benchmark reports |
| Test AI systems against known attack vectors | Built-in benchmark with 79 attacks + 26 safe inputs |
| Apply defense-in-depth for AI systems | 4-layer detection: regex → heuristic → similarity → policy |

---

## Compliance Statement

Aigis is designed to **support organizations' compliance** with the NIST AI Risk Management Framework. As the NIST AI RMF is a voluntary framework, there is no formal certification. Aigis's alignment is demonstrated through:

1. Direct implementation of MEASURE and MANAGE functions
2. Tooling support for GOVERN and MAP functions
3. Open-source transparency enabling external validation
4. Reproducible benchmark results for auditability

Organizations using Aigis can reference this mapping when documenting their AI RMF compliance posture.
