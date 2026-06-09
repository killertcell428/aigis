# Pending: GGUF Model Validation Hardening Guide

**Title:** Supply Chain Hardening: Safe GGUF Model Loading and Validation

**Motivation:**
Two distinct GGUF attack vectors were documented in May–June 2026:
1. **CVE-2026-5760 (CVSS 9.8, SGLang):** Malicious GGUF embeds Jinja2 SSTI payload in `tokenizer.chat_template`; inference server renders it with unsandboxed `jinja2.Environment()`, achieving host-level RCE. Public PoC available; CERT/CC VU#915947.
2. **llama.cpp GGUF parser integer overflow (May 15, 2026):** Integer overflow in the GGML_PAD macro allows a malicious GGUF file to cause arbitrary memory reads before inference begins. Affects Ollama, LM Studio, Jan, and all llama.cpp-backed tools. 156,000+ GGUF files on Hugging Face.

Additionally, Splunk (2026) documented GGUF models on Hugging Face with `chat_template` fields that silently exfiltrate conversation content or override system prompts at inference time (inference-time backdoors that bypass static scanners).

**Research finding:**
`auto-improvement/research/2026-06-02T06-10_5-supply-chain-llm.md` — CVE-2026-5760 and GGUF parser overflow findings.

**Proposed change:**
Create `docs/gguf-model-validation-guide.md` covering:
1. The three attack surfaces in GGUF files: parser vulnerabilities (binary layer), chat template SSTI (metadata layer), inference-time behavioral backdoors (weight layer)
2. Safe loading practices:
   - Verify SHA-256 checksum of GGUF files against Hugging Face model card signatures before loading
   - Use `llama-cpp-python` with the patched GGUF parser (update after May 2026 patch)
   - For SGLang: always use `jinja2.sandbox.ImmutableSandboxedEnvironment` for chat template rendering (CVE-2026-5760 fix)
   - Inspect `tokenizer.chat_template` fields from untrusted models using `gguf-dump` or similar before loading
3. Organizational controls:
   - Maintain an allowlist of approved model sources; require security review for models outside it
   - Never load GGUF files from untrusted repositories without checksum verification
   - Run new models in isolated sandboxes on first load

**Why held back:**
Documentation-only change. The integer overflow is a binary parser issue requiring a software update, not a detection rule. The chat template SSTI is already covered by the new `sc_gguf_template_ssti` pattern added this cycle. The broader behavioral backdoor problem (weight-level tampering) has no regex detection solution.

**Constraint blocking it:**
No implementation needed beyond documentation; deferred to a dedicated documentation cycle.

**Suggested next step for human reviewer:**
Approve a documentation cycle to write `docs/gguf-model-validation-guide.md`. Could be combined with the slopsquatting guide into a single `docs/supply-chain-hardening-guide.md` document covering the full AI model supply chain.
