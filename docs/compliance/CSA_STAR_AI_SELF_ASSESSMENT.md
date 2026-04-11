# Aigis — CSA STAR for AI Level 1 Self-Assessment

> Last updated: 2026-04-10
> Aigis version: v1.3.1
> Reference: [CSA STAR for AI](https://cloudsecurityalliance.org/star/ai)
> Framework: AI Controls Matrix (AICM) + AI Consensus Assessment Initiative Questionnaire (AI-CAIQ)

## Overview

The Cloud Security Alliance (CSA) STAR for AI program provides a framework for demonstrating responsible and auditable AI practices. Level 1 is a self-assessment based on the AI Controls Matrix (AICM) and AI-CAIQ.

This document serves as Aigis's self-assessment against the AICM control domains, preparing for formal STAR for AI Level 1 submission.

## Assessment Summary

| Control Domain | Controls | Compliance Level |
|---------------|:--------:|:----------------:|
| AI Governance & Accountability | 8 | Implemented |
| Data Governance | 6 | Implemented |
| AI Model Development & Training | 5 | N/A (detection tool, not an AI model) |
| AI Security | 10 | **Fully Implemented** |
| AI Privacy | 6 | Implemented |
| Transparency & Explainability | 7 | Implemented |
| Fairness & Bias | 4 | N/A (detection tool, not an AI model) |
| Reliability & Robustness | 6 | **Fully Implemented** |
| Third-Party & Supply Chain | 4 | Implemented |
| Incident Management | 5 | Implemented |

---

## Control Domain Assessments

### 1. AI Governance & Accountability

| Control | Status | Evidence |
|---------|:------:|----------|
| AI governance policies defined | Implemented | YAML policy engine with configurable risk thresholds, actions (block/review/allow), and custom rules per deployment |
| Roles and responsibilities for AI risk | Implemented | Middleware architecture separates security team (policy definition) from development team (integration). Guard class provides clear ownership model |
| AI risk management process | Implemented | 4-layer detection pipeline: normalization → pattern matching → heuristic analysis → similarity detection. Configurable risk levels with documented thresholds |
| Regular review of AI systems | Implemented | Weekly automated research scout identifies new attack vectors. Monthly pattern updates. Built-in benchmark suite for continuous evaluation |
| Documentation of AI decisions | Implemented | Every detection includes structured output: pattern ID, category, risk score, description, OWASP/CWE reference, remediation hint. JSON export for audit trails |
| Stakeholder engagement | Implemented | Open-source model with GitHub Discussions, Issues, and community contributions. Public benchmark results |
| Compliance monitoring | Implemented | `aig benchmark` CLI for automated compliance verification. CI/CD integration support |
| Ethical AI guidelines | Implemented | Detection of harmful content generation, jailbreak prevention, ethical override attempts (6 dedicated patterns) |

### 2. Data Governance

| Control | Status | Evidence |
|---------|:------:|----------|
| Data classification | Implemented | 11 threat categories with risk scoring. PII classified by sensitivity (national IDs: 70-75, phone: 40, postal code: 25) |
| Data protection measures | Implemented | Input scanning prevents PII from reaching LLMs. Output scanning detects PII leakage. 24 PII/confidential detection patterns across 5 countries |
| Data minimization | Implemented | Pattern matching is stateless — no user data is stored or retained by the detection engine. Zero-dependency stdlib implementation |
| Data quality management | Implemented | RAG content scanning (`scan_rag_context()`) validates data quality before insertion into prompts |
| Data lifecycle management | Implemented | Detection operates in-transit only. No data persistence in the scanning pipeline |
| Cross-border data considerations | Implemented | Multi-country PII detection: Japan (マイナンバー, phone, address, bank), Korea (주민등록번호, phone, business reg), China (身份证号, phone, USCC), US (SSN, DL) |

### 3. AI Model Development & Training

| Control | Status | Evidence |
|---------|:------:|----------|
| Model development lifecycle | N/A (detection tool, not an AI model) | Aigis is a detection tool, not an AI model. Pattern development follows research → implement → test → benchmark lifecycle |
| Training data management | N/A (detection tool, not an AI model) | Semantic similarity corpus (56 attack phrases) is curated and versioned. No ML training involved |
| Model validation & testing | **Fully Implemented** | Built-in adversarial benchmark: 79 attacks, 26 safe inputs, 12 categories. 100% precision, 0% false positive rate |
| Version control | **Fully Implemented** | Git-based versioning. Semantic versioning (v0.x.y). CHANGELOG maintained. PyPI releases |
| Reproducibility | **Fully Implemented** | `aig benchmark --json` produces reproducible results. All patterns are deterministic (regex + stdlib) |

### 4. AI Security

| Control | Status | Evidence |
|---------|:------:|----------|
| AI-specific threat modeling | **Fully Implemented** | 83 detection patterns mapped to OWASP LLM Top 10, MITRE ATLAS, and CWE. Covers prompt injection, jailbreak, data exfiltration, PII, command injection, SQL injection, token exhaustion, prompt leak, indirect injection |
| Input validation for AI | **Fully Implemented** | 112 input patterns with 4-layer detection: regex → heuristic → similarity → policy |
| Output validation for AI | **Fully Implemented** | 7 output patterns covering PII leak, secret leak, harmful content |
| Adversarial attack defense | **Fully Implemented** | Text normalization (NFKC, zero-width removal), encoding bypass detection, token manipulation defense. Benchmark: 100% attack detection |
| AI supply chain security | Implemented | Zero-dependency design (Python stdlib only). No external model downloads. No ML pipeline vulnerabilities |
| Secure AI deployment | Implemented | Middleware integration (FastAPI, LangChain, LangGraph). Environment-specific policy configuration |
| AI access control | Implemented | Policy-based access control: block/review/allow per risk level. Custom rules per organization |
| AI monitoring & logging | Implemented | Structured `CheckResult`/`ScanResult` output with JSON serialization. Integration with SIEM/logging systems |
| Incident detection | **Fully Implemented** | Real-time threat detection with category, severity, and remediation. CRITICAL-level alerts for highest-risk patterns |
| Vulnerability management | Implemented | Weekly research scout for new attack vectors. Community-driven pattern contributions via GitHub |

### 5. AI Privacy

| Control | Status | Evidence |
|---------|:------:|----------|
| Privacy impact assessment | Implemented | Aigis performs PII detection as a core function, enabling organizations to conduct privacy impact assessments on AI inputs/outputs |
| PII detection and protection | **Fully Implemented** | 17 input PII patterns + 5 output PII patterns across 5 countries. Covers national IDs, phone numbers, financial data, addresses, credentials |
| Consent management | Implemented | Policy engine supports custom rules for consent-based data handling |
| Data subject rights | Implemented | Stateless detection — no user data retention. No data subject concerns in the scanning pipeline |
| Cross-border transfer safeguards | Implemented | Multi-jurisdiction PII detection enables organizations to enforce data residency policies |
| Privacy by design | **Fully Implemented** | Zero-dependency, stateless architecture. No data persistence. No cloud calls for detection (offline-capable) |

### 6. Transparency & Explainability

| Control | Status | Evidence |
|---------|:------:|----------|
| AI decision transparency | **Fully Implemented** | Every detection includes: pattern ID, human-readable name, description, category, risk score, OWASP/CWE reference, remediation hint |
| Explainable detection results | **Fully Implemented** | `MatchedRule` output shows exactly which pattern matched, what text triggered it, and why it's a risk |
| Documentation of AI capabilities | **Fully Implemented** | OWASP LLM Top 10 coverage matrix, MITRE ATLAS mapping, NIST AI RMF alignment — all publicly available |
| Open-source transparency | **Fully Implemented** | Full source code on GitHub. MIT license. All patterns inspectable and auditable |
| Benchmark reproducibility | **Fully Implemented** | `aig benchmark` CLI produces deterministic, reproducible results |
| Version and change tracking | **Fully Implemented** | Semantic versioning, CHANGELOG, git history, PyPI release notes |
| Stakeholder communication | Implemented | GitHub Discussions, Issues, documentation site, Zenn/DEV.to articles |

### 7. Fairness & Bias

| Control | Status | Evidence |
|---------|:------:|----------|
| Bias assessment | N/A (detection tool, not an AI model) | Aigis is a rule-based detection system (no ML), minimizing bias risk. Pattern design reviewed for cultural sensitivity |
| Multilingual fairness | Implemented | Equal detection capability across 4 languages (EN, JA, KO, ZH). Same pattern categories and scoring thresholds across all languages |
| False positive mitigation | **Fully Implemented** | Signal word verification prevents false positives. Benchmark: 0/26 safe inputs flagged (0% FP rate). Diminishing returns scoring prevents over-flagging |
| Regular fairness review | Implemented | Benchmark includes diverse safe inputs across languages. FP rate tracked per release |

### 8. Reliability & Robustness

| Control | Status | Evidence |
|---------|:------:|----------|
| System reliability | **Fully Implemented** | Zero-dependency (Python stdlib only). No external API calls. No network dependencies. Offline-capable |
| Performance benchmarking | **Fully Implemented** | 79/79 attack detection (100%), 0/26 false positives (0%). Benchmark reproducible via CLI |
| Adversarial robustness | **Fully Implemented** | Text normalization (NFKC, zero-width, fullwidth), encoding bypass detection, multi-layer defense (regex + heuristic + similarity + policy) |
| Graceful degradation | Implemented | Policy engine supports fallback actions. Pattern matching is deterministic — no stochastic failures |
| Continuous testing | Implemented | CI/CD integration via `aig benchmark`. Weekly automated testing via research scout triggers |
| Recovery procedures | Implemented | Stateless design — no state to recover. Policy rollback via YAML version control |

### 9. Third-Party & Supply Chain

| Control | Status | Evidence |
|---------|:------:|----------|
| Third-party AI risk assessment | Implemented | `scan_rag_context()` scans third-party content before insertion. Indirect injection detection for RAG/web scraping |
| Supply chain security | **Fully Implemented** | Zero external dependencies. No ML model downloads. No third-party API calls. Pure Python stdlib |
| Vendor management | Implemented | No vendors in the detection pipeline. Integration points (LangChain, FastAPI) are optional |
| Component inventory | Implemented | Single `pyproject.toml` with zero runtime dependencies. Development dependencies tracked and version-pinned |

### 10. Incident Management

| Control | Status | Evidence |
|---------|:------:|----------|
| AI incident detection | **Fully Implemented** | Real-time detection across 11 threat categories. Structured alerts with severity levels |
| Incident response procedures | Implemented | Policy engine automates response: block (reject), review (queue for human), allow (pass). Remediation hints guide response |
| Incident documentation | Implemented | Structured JSON output for every detection event. Compatible with SIEM/incident management systems |
| Post-incident analysis | Implemented | Benchmark suite enables post-incident regression testing. Pattern additions driven by incident analysis |
| Continuous improvement | Implemented | Weekly research scout → pattern development → benchmark validation cycle |

---

## Next Steps for Formal Submission

1. **Complete AI-CAIQ questionnaire** using this self-assessment as the basis
2. **Submit to CSA STAR Registry** at [cloudsecurityalliance.org/star/registry](https://cloudsecurityalliance.org/star/registry)
3. **Obtain Valid-AI-ted badge** for public display on website and documentation
4. **Annual renewal** with updated self-assessment

### Level 2 Preparation (Future)

CSA STAR for AI Level 2 requires:
- ISO 42001 certification (prerequisite)
- Third-party audit of AI controls
- Continuous monitoring and reporting

Timeline: Target after ISO 42001 certification (Phase 3 of compliance roadmap).

---

## Compliance Statement

This self-assessment demonstrates Aigis's alignment with the CSA AI Controls Matrix across all 10 control domains. Aigis's zero-dependency, stateless, open-source architecture provides inherent advantages in security, privacy, transparency, and supply chain risk management.

Aigis is preparing for formal CSA STAR for AI Level 1 registration.
