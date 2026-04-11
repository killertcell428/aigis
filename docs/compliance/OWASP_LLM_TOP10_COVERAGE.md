# Aigis — OWASP Top 10 for LLM Applications (2025) Coverage Matrix

> Last updated: 2026-04-10
> Aigis version: v1.3.1 (165+ patterns + active decoding + capabilities + AEP + safety verification)
> Reference: [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/)

## Coverage Summary

| # | Risk | Coverage | Patterns | Detection Layer |
|---|------|:--------:|----------|-----------------|
| LLM01 | Prompt Injection | **Full** | 29 patterns | Regex + Similarity + Heuristic |
| LLM02 | Sensitive Information Disclosure | **Full** | 24 patterns | Regex (Input + Output) |
| LLM03 | Supply Chain Vulnerabilities | Out of Scope | — | Requires model registry / SBOM tooling (not runtime scanning) |
| LLM04 | Data and Model Poisoning | Out of Scope (RAG covered) | 5 patterns | RAG/indirect poisoning detected; model weight poisoning requires model audit infrastructure |
| LLM05 | Improper Output Handling | **Full** | 7 patterns | Output filter |
| LLM06 | Excessive Agency | **Strong** | 5 patterns | Tool abuse + indirect injection |
| LLM07 | System Prompt Leakage | **Full** | 12 patterns | Regex + Similarity |
| LLM08 | Vector and Embedding Weaknesses | **Strong** | 5 patterns | `scan_rag_context()` API |
| LLM09 | Misinformation | Out of Scope | — | Requires model-level fact verification (not pattern matching) |
| LLM10 | Unbounded Consumption | **Full** | 5 patterns | Regex + Heuristic |

**Full coverage of all runtime-detectable risks (8/10). The remaining 2 (Supply Chain, Model Poisoning) fall within infrastructure domains such as model registries and cryptographic verification, and are outside the scope of input/output scanning tools. 165+ patterns.**

---

## Detailed Mapping

### LLM01: Prompt Injection

**Coverage: Full** — Direct and indirect injection detection with multilingual support.

| Sub-category | Pattern Count | Languages | Pattern IDs |
|--------------|:------------:|-----------|-------------|
| Instruction Override | 5 | EN, JA, KO, ZH | `pi_ignore_instructions`, `pi_new_instructions`, `pi_jp_ignore`, `pi_ko_ignore`, `pi_zh_ignore` |
| Jailbreak / DAN | 7 | EN | `pi_jailbreak_dan`, `jb_evil_roleplay`, `jb_no_restrictions`, `jb_fictional_bypass`, `jb_grandma_exploit`, `jb_developer_mode`, `jb_ignore_ethics` |
| Role Switch | 4 | EN, JA, KO, ZH | `pi_role_switch`, `pi_jp_role_switch`, `pi_ko_role_switch`, `pi_zh_role_switch` |
| Encoding Bypass | 1 | EN | `pi_encoding_bypass` |
| Restriction Bypass | 3 | JA, KO, ZH | `pi_jp_restriction_bypass`, `pi_ko_restriction_bypass`, `pi_zh_restriction_bypass` |
| Indirect Injection (RAG) | 5 | EN | `ii_hidden_instruction`, `ii_context_poisoning`, `ii_exfil_via_markdown`, `ii_invisible_text`, `ii_tool_abuse` |
| Semantic Similarity | 56 phrases | EN, JA, KO, ZH | Fuzzy matching via `similarity.py` |

**Detection layers:**
1. Regex pattern matching (112 patterns)
2. Semantic similarity detection (56 canonical attack phrases, 4 languages)
3. Token exhaustion heuristic (repetition ratio analysis)
4. Text normalization (NFKC, zero-width character removal)

### LLM02: Sensitive Information Disclosure

**Coverage: Full** — Input-side PII prevention + output-side leak detection.

| Sub-category | Direction | Pattern Count | Pattern IDs |
|--------------|-----------|:------------:|-------------|
| National IDs | Input | 4 | `pii_jp_my_number`, `pii_ssn_input`, `pii_ko_rrn`, `pii_zh_national_id` |
| Phone Numbers | Input | 3 | `pii_jp_phone`, `pii_ko_phone`, `pii_zh_phone` |
| Financial Data | Input | 4 | `pii_credit_card_input`, `pii_jp_bank_account`, `pii_ko_business_reg`, `pii_zh_uscc` |
| Credentials | Input | 3 | `pii_api_key_input`, `conf_password_literal`, `conf_connection_string` |
| PII in Output | Output | 5 | `out_pii_ssn`, `out_pii_credit_card`, `out_pii_email_bulk`, `out_pii_jp_my_number`, `out_pii_jp_phone` |
| Secrets in Output | Output | 1 | `out_secret_leak` |
| Data Exfiltration | Input | 4 | `exfil_pii_request`, `exfil_api_keys`, `exfil_send_to_external`, `exfil_keyword` |

### LLM03: Supply Chain Vulnerabilities

**Coverage: Out of Scope** — Not addressable by runtime input/output scanning.

Supply chain security requires model provenance registries, dependency SBOM (Software Bill of Materials) tooling, and package integrity verification — capabilities that operate at the infrastructure/CI level, not at the LLM request level.

Aigis provides complementary support:
- YAML-based policy engine for custom supply chain rules
- Zero-dependency design eliminates Aigis itself as a supply chain risk

### LLM04: Data and Model Poisoning

**Coverage: RAG Poisoning Covered / Model Weight Poisoning Out of Scope**

Model weight and training data poisoning require cryptographic attestation and model auditing infrastructure — not runtime scanning. However, Aigis fully covers **data poisoning via RAG** (the most common vector in production).

| Sub-category | Pattern Count | Pattern IDs |
|--------------|:------------:|-------------|
| Context Poisoning | 1 | `ii_context_poisoning` |
| Hidden Instructions in Data | 1 | `ii_hidden_instruction` |
| Invisible Text Injection | 1 | `ii_invisible_text` |
| Markdown/HTML Exfil | 1 | `ii_exfil_via_markdown` |
| Tool Abuse via Poisoned Data | 1 | `ii_tool_abuse` |

**API:** `scan_rag_context()` applies all 112 input patterns to retrieved documents.

### LLM05: Improper Output Handling

**Coverage: Full** — Output filter with 7 patterns.

| Sub-category | Pattern Count | Pattern IDs |
|--------------|:------------:|-------------|
| PII in Output | 5 | `out_pii_ssn`, `out_pii_credit_card`, `out_pii_email_bulk`, `out_pii_jp_my_number`, `out_pii_jp_phone` |
| Secret Leak | 1 | `out_secret_leak` (OpenAI, Google, GitHub, Slack keys) |
| Harmful Content | 1 | `out_harmful_instructions` |

### LLM06: Excessive Agency

**Coverage: Strong** — Tool/function call injection detection.

| Sub-category | Pattern Count | Pattern IDs |
|--------------|:------------:|-------------|
| Tool Call Injection | 1 | `ii_tool_abuse` |
| Data Exfiltration via Agency | 4 | `exfil_send_to_external`, `exfil_keyword`, `ii_exfil_via_markdown`, `exfil_api_keys` |

**Mitigation:** Aigis can be deployed as a middleware layer (FastAPI, LangChain, LangGraph) to intercept and validate inputs before they reach tool-calling agents.

### LLM07: System Prompt Leakage

**Coverage: Full** — Dedicated prompt leak detection in 4 languages.

| Sub-category | Pattern Count | Pattern IDs |
|--------------|:------------:|-------------|
| Verbatim Extraction | 4 | `pl_verbatim_repeat`, `pl_starting_with`, `pl_output_instructions_verbatim`, `pl_repeat_back_verbatim` |
| Indirect Inquiry | 2 | `pl_what_were_you_told`, `pl_forget_and_ask` |
| System Prompt Extraction | 4 | `pi_system_prompt_leak`, `pi_jp_system_prompt`, `pi_ko_system_prompt`, `pi_zh_system_prompt` |
| Japanese Prompt Leak | 2 | `pl_ja_verbatim`, `pl_ja_what_told` |

### LLM08: Vector and Embedding Weaknesses

**Coverage: Strong** — RAG-specific scanning API.

Aigis provides `scan_rag_context()` which applies all 112 input patterns + 5 indirect injection patterns to retrieved document chunks before they enter the prompt.

**Detection capabilities:**
- Hidden instructions in retrieved documents
- Context poisoning attempts
- Invisible text (HTML comments, hidden elements)
- Data exfiltration via markdown images in RAG output

### LLM09: Misinformation

**Coverage: Out of Scope** — Requires model-level fact verification.

Misinformation detection requires semantic understanding and factual verification at the model level — fundamentally different from pattern-based input/output scanning. No scanning tool can determine if an LLM's output is factually correct.

**Complementary support:** Custom policy rules can flag categories that require human review before publishing.

### LLM10: Unbounded Consumption

**Coverage: Full** — Token exhaustion and resource abuse detection.

| Sub-category | Pattern Count | Pattern IDs |
|--------------|:------------:|-------------|
| Repetition Flooding | 2 | `te_repetition_flood_en`, `te_repetition_flood_ja` |
| Buried Instructions | 1 | `te_ignore_prefix_buried` |
| Unicode Noise | 1 | `te_unicode_noise` |
| Null Byte Stuffing | 1 | `te_null_byte_stuffing` |
| Heuristic | 1 | Length + repetition ratio check (>2000 chars, >35% repetition) |

---

## Benchmark Results

```
Aigis Detection Benchmark (v1.0.0)
=========================================================
Category                Tests  Detected  Missed  Precision
---------------------------------------------------------
prompt_injection           10        10       0     100.0%
jailbreak                  15        15       0     100.0%
sql_injection               8         8       0     100.0%
prompt_leak                 8         8       0     100.0%
token_exhaustion            3         3       0     100.0%
prompt_injection_ko         5         5       0     100.0%
prompt_injection_zh         7         7       0     100.0%
encoding_bypass             3         3       0     100.0%
memory_poisoning            4         4       0     100.0%
second_order_injection      4         4       0     100.0%
mcp_poisoning               8         8       0     100.0%
indirect_injection          8         8       0     100.0%
pii_input                   5         5       0     100.0%
pii_input_ko                3         3       0     100.0%
pii_input_zh                3         3       0     100.0%
data_exfiltration           4         4       0     100.0%
---------------------------------------------------------
TOTAL                      98        98       0     100.0%

False positive rate: 0/26 safe inputs flagged (0.0%)
```

---

## How to Verify

```python
from aigis.benchmark import BenchmarkSuite

suite = BenchmarkSuite()
results = suite.run()
print(results.summary())
```

```bash
aig benchmark
aig benchmark --category prompt_injection
aig benchmark --json
```
