# Aigis — MITRE ATLAS Coverage Matrix

> Last updated: 2026-07-08
> Aigis version: v1.1.11
> Reference: [MITRE ATLAS](https://atlas.mitre.org/) (current matrix)
> Companion: [ATR_CROSSWALK.md](./ATR_CROSSWALK.md)

## Overview

MITRE ATLAS (Adversarial Threat Landscape for AI Systems) catalogs adversarial
tactics and techniques against AI systems. This document maps Aigis detection
patterns to current official ATLAS technique IDs.

> **Note on prior version:** The previous revision of this document used an
> older, non-standard numbering scheme (e.g. AML.T0057 was labelled "LLM Plugin
> Compromise"; AML.T0066–T0072 were introduced as custom identifiers not present
> in the official ATLAS matrix). This revision aligns all IDs to the current
> official ATLAS matrix. See [ATR_CROSSWALK.md](./ATR_CROSSWALK.md) for the
> verified crosswalk that surfaced the drift.

---

## Coverage Summary

| ATLAS Tactic | Covered techniques |
|---|---|
| Initial Access | AML.T0051, AML.T0051.001, AML.T0054, AML.T0056 |
| Execution | AML.T0053, AML.T0050 |
| Persistence | AML.T0080 |
| Defense Evasion | AML.T0054 (jailbreak bypass), normalisation layer |
| Credential Access | AML.T0056, AML.T0057 |
| Lateral Movement | AML.T0070 |
| Collection | AML.T0024, AML.T0025 |
| Exfiltration | AML.T0024, AML.T0025, AML.T0057 |
| Impact | AML.T0029, AML.T0105 |
| Supply Chain | AML.T0010, AML.T0109, AML.T0110 |

**Runtime-detectable techniques with Aigis coverage: 15 confirmed (see
[ATR_CROSSWALK.md](./ATR_CROSSWALK.md) §crosswalk for the verified table).**

Techniques not covered by Aigis are either (a) training-time / model-artifact /
infrastructure techniques that fall outside input/output scanning, or (b) runtime
gaps documented in ATR_CROSSWALK.md §gap-analysis-b.

---

## Detailed Technique Mapping

### Initial Access

| ATLAS ID | Technique | Aigis Coverage | Patterns |
|---|---|:---:|---|
| AML.T0051 | LLM Prompt Injection | **Full** | `pi_ignore_instructions`, `pi_new_instructions`, `pi_role_switch` (EN/JA/KO/ZH), `pi_jailbreak_dan`, similarity detection |
| AML.T0051.001 | LLM Prompt Injection: Indirect | **Full** | `ii_context_poisoning`, `ii_hidden_instruction`, `ii_invisible_text`, `ii_tool_abuse` + `scan_rag_context()` API |
| AML.T0054 | LLM Jailbreak | **Full** | `jb_evil_roleplay`, `jb_no_restrictions`, `jb_fictional_bypass`, `jb_grandma_exploit`, `jb_developer_mode`, `jb_ignore_ethics` |
| AML.T0056 | Extract LLM System Prompt | **Full** | `pi_system_prompt_leak`, `pl_repeat_back_verbatim`, `pl_*` prompt-leak family (4 languages) |

### Execution

| ATLAS ID | Technique | Aigis Coverage | Patterns |
|---|---|:---:|---|
| AML.T0053 | AI Agent Tool Invocation | **Full** | `ii_tool_abuse` detects manipulated or unauthorised tool/function calls |
| AML.T0050 | Command and Scripting Interpreter | **Full** | `cmdi_shell`, `cmdi_path_traversal` |

### Persistence

| ATLAS ID | Technique | Aigis Coverage | Patterns |
|---|---|:---:|---|
| AML.T0080 | AI Agent Context Poisoning | **Full** | `mem_cross_session_persistence`, `mem_experience_hijack` |

### Collection / Exfiltration

| ATLAS ID | Technique | Aigis Coverage | Patterns |
|---|---|:---:|---|
| AML.T0057 | LLM Data Leakage | **Full** | `out_secret_leak`, `out_pii_ssn`, `out_pii_credit_card`, `out_pii_email_bulk`, `exfil_api_keys`, 17 PII input patterns |
| AML.T0024 | Exfiltration via AI Inference API | **Full** | `exfil_send_to_external`, `exfil_api_keys`, `exfil_pii_request` |
| AML.T0025 | Exfiltration via Cyber Means | **Full** | `ii_exfil_via_markdown` (markdown image beacon / HTML img), `exfil_send_to_external` |
| AML.T0070 | RAG Poisoning | **Full** | `ii_context_poisoning` + `scan_rag_context()` API |

### Impact

| ATLAS ID | Technique | Aigis Coverage | Patterns |
|---|---|:---:|---|
| AML.T0029 | Denial of ML Service | **Full** | `te_repetition_flood_en`, `te_repetition_flood_ja`, `te_ignore_prefix_buried`, token exhaustion heuristic |
| AML.T0105 | Escape to Host | **Full** | `se_container_escape`, `afe_python_mro_escape` |

### Supply Chain

| ATLAS ID | Technique | Aigis Coverage | Patterns |
|---|---|:---:|---|
| AML.T0010 | AI Supply Chain Compromise | **Full** | `sc_compromised_pkg_version` |
| AML.T0110 | AI Agent Tool Poisoning | **Full** | `mcp_cross_tool_shadow` and `mcp_*` scanner family |
| AML.T0109 | AI Supply Chain Rug Pull | **Full** | `mcp_rug_pull_indicator` |

---

## Runtime Gaps (no Aigis pattern yet)

These ATLAS techniques are runtime-detectable in principle but Aigis has no
pattern for them today. Contributed patterns welcome.

| ATLAS ID | Technique | Why detectable | Gap filed |
|---|---|---|---|
| AML.T0069 | Discover LLM System Information | Recon prompts enumerating tool schemas are screenable input patterns | [#166](https://github.com/killertcell428/aigis/issues/166) |
| AML.T0060 | Publish Hallucinated Entities | Hallucinated package names in output, matchable against a package-name heuristic | — |
| AML.T0102 | Generate Malicious Commands | Output-side generation of harmful command strings | — |
| AML.T0104 | Publish Poisoned AI Agent Tool | Malicious tool/skill manifest, screenable in `mcp_scanner` | — |
| AML.T0034 | Cost Harvesting | Token/compute exhaustion for cost damage; related to `te_*` DoS family | — |

---

## Out-of-scope techniques

The following ATLAS techniques concern training data, model artifacts, model
access, or pre-interaction infrastructure. They are correctly outside Aigis's
input/output scanning scope.

AML.T0011, AML.T0018, AML.T0019, AML.T0020, AML.T0036, AML.T0040,
AML.T0043, AML.T0044, AML.T0046, AML.T0047, AML.T0048, AML.T0049,
AML.T0052, AML.T0055.

---

## Detection Architecture vs. ATLAS Kill Chain

```
ATLAS Kill Chain Stage          Aigis Defense Layer
──────────────────────────────────────────────────────────
Reconnaissance                  [Out of Scope] Pre-LLM attacker activity
Resource Development            [Out of Scope] Attack infrastructure (external)
Initial Access                  ██████████ T0051 / T0051.001 / T0054 / T0056
ML Model Access                 [Out of Scope] Infrastructure authentication
Execution                       ██████████ T0053 / T0050
Persistence                     ██████████ T0080
Defense Evasion                 ██████████ Normalisation + jailbreak prevention
Credential Access               ██████████ T0056 / T0057
Lateral Movement                ██████████ T0070 (RAG poisoning)
Collection                      ██████████ T0024 / T0025 / T0057
Exfiltration                    ██████████ T0024 / T0025 (markdown / API path)
Impact                          ██████████ T0029 / T0105
Supply Chain                    ██████████ T0010 / T0109 / T0110
```

---

## Compliance Statement

Aigis provides technical controls aligned with MITRE ATLAS adversarial techniques
for AI systems. All technique IDs in this document are anchored to the current
official ATLAS matrix.

- **15 runtime-detectable techniques covered**, verified against source patterns
  and cross-referenced with Agent Threat Rules (ATR) — see
  [ATR_CROSSWALK.md](./ATR_CROSSWALK.md).
- **5 runtime gaps documented** above; contributions welcome.
- **14 out-of-scope techniques** correctly outside input/output scanning.
- Pattern set updated continuously; see `CHANGELOG.md` for per-cycle additions.
