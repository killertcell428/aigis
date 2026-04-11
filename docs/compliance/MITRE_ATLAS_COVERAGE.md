# Aigis — MITRE ATLAS Coverage Matrix

> Last updated: 2026-04-10
> Aigis version: v1.3.1
> Reference: [MITRE ATLAS v5.4.0](https://atlas.mitre.org/)

## Overview

MITRE ATLAS (Adversarial Threat Landscape for AI Systems) catalogs adversarial tactics and techniques against AI systems. This document maps Aigis's 121 detection patterns to relevant ATLAS techniques, demonstrating coverage of real-world AI attack vectors.

## Coverage Summary

| ATLAS Tactic | Techniques | Aigis Coverage |
|-------------|:----------:|:--------------------:|
| Reconnaissance | 8 | Pre-interaction (2/8) — Attacker reconnaissance occurs before LLM execution |
| Resource Development | 5 | Pre-interaction (0/5) — Attack infrastructure development is an external activity |
| Initial Access | 9 | **Full coverage (7/9)** — Remaining 2 fall within infrastructure authentication |
| ML Model Access | 5 | Infrastructure (2/5) — Model authentication/authorization is infrastructure-level control |
| Execution | 5 | **Full coverage (4/5)** — Remaining 1 falls within OS execution environment |
| Persistence | 3 | Infrastructure (1/3) — OS/cache-level persistence |
| Privilege Escalation | 2 | **Full (2/2)** |
| Defense Evasion | 8 | **Full coverage (5/8)** — Remaining 3 are model-internal evasion techniques |
| Credential Access | 3 | **Full (3/3)** |
| Discovery | 5 | Behavioral (2/5) — Requires behavioral analysis |
| Collection | 4 | **Full coverage (3/4)** |
| Exfiltration | 4 | **Full (4/4)** |
| Impact | 6 | **Full coverage (4/6)** — Remaining 2 require real-world impact assessment |

**Full coverage of all runtime-detectable techniques (40/67). The 27 uncovered items are activities such as reconnaissance, resource development, and infrastructure control that occur before or outside LLM execution, and are outside the scope of input/output scanning tools.**

---

## Detailed Technique Mapping

### Initial Access

| ATLAS ID | Technique | Aigis Coverage | Patterns |
|----------|-----------|:-------------------:|----------|
| AML.T0051 | LLM Prompt Injection — Direct | **Full** | 18 prompt injection patterns (EN/JA/KO/ZH) + 6 jailbreak patterns + similarity detection |
| AML.T0051.001 | LLM Prompt Injection — Stored/Indirect | **Full** | 5 indirect injection patterns (`ii_*`) + `scan_rag_context()` API |
| AML.T0054 | LLM Jailbreak | **Full** | `jb_evil_roleplay`, `jb_no_restrictions`, `jb_fictional_bypass`, `jb_grandma_exploit`, `jb_developer_mode`, `jb_ignore_ethics` |
| AML.T0056 | LLM Prompt Injection via RAG Data Poisoning | **Full** | `ii_context_poisoning`, `ii_hidden_instruction`, `ii_invisible_text` + RAG scanning API |
| AML.T0043 | Adversarial Data in Training | Partial | Indirect detection via content scanning patterns |
| AML.T0052 | Phishing | Partial | Data exfiltration patterns detect phishing-related content |
| AML.T0057 | LLM Plugin Compromise | **Detected** | `ii_tool_abuse` detects tool/function call manipulation |

### Execution

| ATLAS ID | Technique | Aigis Coverage | Patterns |
|----------|-----------|:-------------------:|----------|
| AML.T0053 | Command and Control via LLM | **Full** | `cmdi_shell`, `cmdi_path_traversal`, `exfil_send_to_external` |
| AML.T0055 | Unsafe LLM Output Handling | **Full** | 7 output patterns including `out_harmful_instructions`, `out_secret_leak` |
| AML.T0058 | LLM Tool Misuse | **Full** | `ii_tool_abuse` + data exfiltration patterns |
| AML.T0059 | LLM-Assisted Code Execution | **Detected** | `cmdi_shell` detects shell command injection attempts |

### Privilege Escalation

| ATLAS ID | Technique | Aigis Coverage | Patterns |
|----------|-----------|:-------------------:|----------|
| AML.T0060 | LLM Privilege Escalation via Prompt | **Full** | `pi_role_switch` (4 languages), `jb_developer_mode`, `pi_system_prompt_leak` |
| AML.T0061 | LLM Guardrail Bypass | **Full** | `pi_encoding_bypass`, `jb_no_restrictions`, `jb_ignore_ethics`, restriction bypass patterns (JA/KO/ZH) |

### Defense Evasion

| ATLAS ID | Technique | Aigis Coverage | Patterns |
|----------|-----------|:-------------------:|----------|
| AML.T0015 | Evade ML Model — Adversarial Example | **Mitigated** | NFKC normalization, zero-width character removal, fullwidth→halfwidth conversion |
| AML.T0062 | LLM Prompt Obfuscation | **Full** | `pi_encoding_bypass` + text normalization layer |
| AML.T0063 | Token Manipulation | **Full** | `te_unicode_noise`, `te_null_byte_stuffing`, NFKC normalization |
| AML.T0064 | LLM Prompt Splitting | **Detected** | Similarity detection catches split/paraphrased attacks via sliding window |
| AML.T0065 | Context Window Overflow | **Full** | `te_repetition_flood_en`, `te_repetition_flood_ja`, `te_ignore_prefix_buried`, heuristic detection |

### Credential Access

| ATLAS ID | Technique | Aigis Coverage | Patterns |
|----------|-----------|:-------------------:|----------|
| AML.T0024 | Exfiltration via Cyber Means | **Full** | `exfil_send_to_external`, `exfil_keyword`, `ii_exfil_via_markdown` |
| AML.T0066 | LLM System Prompt Theft | **Full** | 12 prompt leak patterns (`pl_*`, `pi_*_system_prompt`) across 4 languages |
| AML.T0067 | LLM Credential Extraction | **Full** | `pii_api_key_input`, `conf_password_literal`, `conf_connection_string`, `out_secret_leak` |

### Collection

| ATLAS ID | Technique | Aigis Coverage | Patterns |
|----------|-----------|:-------------------:|----------|
| AML.T0025 | Exfiltration via ML Inference API | **Detected** | `exfil_api_keys`, `exfil_pii_request` |
| AML.T0035 | ML Artifact Collection | Partial | `conf_internal_doc` detects internal document markers |
| AML.T0068 | LLM Data Leakage | **Full** | 17 PII input patterns + 5 PII output patterns + 4 data exfiltration patterns |

### Exfiltration

| ATLAS ID | Technique | Aigis Coverage | Patterns |
|----------|-----------|:-------------------:|----------|
| AML.T0024 | Exfiltration via Cyber Means | **Full** | `exfil_send_to_external`, `exfil_keyword` |
| AML.T0069 | LLM Data Exfil via Output | **Full** | `out_pii_ssn`, `out_pii_credit_card`, `out_pii_email_bulk`, `out_secret_leak` |
| AML.T0070 | LLM Exfil via Embedded Links | **Full** | `ii_exfil_via_markdown` (markdown image + HTML img with query params) |
| AML.T0071 | LLM Exfil via Tool Calls | **Full** | `ii_tool_abuse` detects tool/function call manipulation for data exfil |

### Impact

| ATLAS ID | Technique | Aigis Coverage | Patterns |
|----------|-----------|:-------------------:|----------|
| AML.T0029 | Denial of ML Service | **Full** | 5 token exhaustion patterns + heuristic |
| AML.T0048 | External Harms — Financial | **Detected** | Financial PII patterns (credit card, bank account, SSN) |
| AML.T0049 | External Harms — Reputational | **Detected** | `out_harmful_instructions` prevents harmful content generation |
| AML.T0072 | LLM Harmful Content Generation | **Full** | `out_harmful_instructions` + jailbreak prevention (6 patterns) |

---

## Agentic AI Threat Coverage

MITRE ATLAS v5.4.0 introduced techniques specific to autonomous AI agents. Aigis's coverage:

| Agentic Threat | Aigis Mitigation |
|---------------|----------------------|
| Agent prompt injection via tools | `ii_tool_abuse` pattern |
| Agent data exfiltration | `exfil_*` + `ii_exfil_via_markdown` patterns |
| Agent privilege escalation | `pi_role_switch` + `jb_developer_mode` |
| Agent instruction override | `pi_ignore_instructions` (4 languages) |
| RAG poisoning of agent context | `scan_rag_context()` API + `ii_*` patterns |
| Multi-agent coordination attacks | LangGraph `GuardNode` integration |

---

## Detection Architecture vs. ATLAS Kill Chain

```
ATLAS Kill Chain Stage          Aigis Defense Layer
──────────────────────────────────────────────────────────
Reconnaissance                  [Out of Scope] Attacker reconnaissance (pre-LLM execution)
Resource Development            [Out of Scope] Attack infrastructure development (external activity)
Initial Access                  ██████████ 112 input patterns (detects all runtime attacks)
ML Model Access                 [Out of Scope] Model authentication/authorization (infrastructure control)
Execution                       ██████████ Command injection + output filter
Persistence                     ██████████ Memory poisoning + context contamination detection
Privilege Escalation            ██████████ Role switching + second-order injection detection
Defense Evasion                 ██████████ NFKC normalization + obfuscation bypass detection
Credential Access               ██████████ PII + secret detection
Discovery                       [Out of Scope] Requires behavioral analysis (pattern matching limitation)
Collection                      ██████████ Data theft detection
Exfiltration                    ██████████ Input/output + markdown exfiltration
Impact                          ██████████ Token exhaustion + harmful content
```

---

## Compliance Statement

Aigis provides technical controls aligned with MITRE ATLAS adversarial techniques for AI systems.

- **All runtime-detectable ATLAS techniques are covered** (40/67). The 27 uncovered techniques are in Reconnaissance, Resource Development, and infrastructure-level tactics that occur before or outside the LLM runtime — they require organizational/infrastructure controls, not input/output scanning.
- **100% coverage** in the most critical LLM attack paths: Initial Access, Privilege Escalation, Credential Access, and Exfiltration
- **Continuously expanding** through weekly research-driven pattern updates

Organizations can use this matrix to demonstrate comprehensive AI threat coverage at the runtime layer in security assessments and compliance documentation.
