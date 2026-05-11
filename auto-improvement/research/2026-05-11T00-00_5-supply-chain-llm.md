# Supply Chain LLM — Research Note (Second Pass)

**Cycle:** 5 (second pass) · **Domain:** supply-chain-llm · **UTC:** 2026-05-11T00-00

Prior coverage (2026-05-08T12-10): LiteLLM/TeamPCP compromise, slopsquatting,
malicious LLM API routers, pickle deserialization, skill ecosystem poisoning.
This pass focuses on **framework-level deserialization CVEs, model-config
code execution, and vulnerable PyTorch versions**.

---

## Findings

- **CVE-2025-68664 — LangChain Core serialization injection (CVSS 9.3).**
  `langchain_core.load.serializable.loads()` deserializes arbitrary LangChain
  objects from JSON that carries an `"lc":"1"` type marker. An attacker submits
  crafted JSON via user input; the chain calls `loads()` on it and instantiates
  dangerous components (e.g., a `BashChain`) without authentication. Affects
  all langchain-core < 1.2.5 and < 0.3.81 on the 0.3.x branch (CVSS 9.3).
  CVE-2025-68665 is the parallel JavaScript (langchain.js) variant.
  **aigis takeaway:** Detect `langchain_core.loads(` calls and JSON payloads
  containing the `"lc":"1"` deserialization marker in untrusted input.
  - Source: <https://github.com/advisories/GHSA-c67j-w6g6-q2cm>
  - Source: <https://thehackernews.com/2025/12/critical-langchain-core-vulnerability.html>

- **CVE-2025-32434 — PyTorch RCE bypassing weights_only=True (CVSS 9.3).**
  PyTorch ≤ 2.5.1 contains an RCE vulnerability that can be triggered via
  `torch.load()` even when `weights_only=True` is specified. The attack exploits
  a flaw in the restricted unpickle deserializer that can be bypassed via crafted
  tensor storage objects. Patched in PyTorch 2.6.0.  This is distinct from the
  general unsafe-pickle rule already in aigis (which catches `torch.load()`
  _without_ `weights_only=True`); 2.5.1 is vulnerable regardless.
  **aigis takeaway:** Add torch 2.5.0–2.5.1 to the `sc_compromised_pkg_version`
  known-bad version database so agents asking to install these versions are flagged.
  - Source: <https://nvd.nist.gov/vuln/detail/CVE-2025-32434>

- **CVE-2025-23304 — Hugging Face NeMo / Hydra _target_ instantiation (CVSS ~8.8).**
  Poisoned NeMo model-config files (`.nemo`, `.yaml`) embed a Hydra
  `_target_: os.system` directive. When the victim loads the config with
  `hydra.utils.instantiate()`, the OS call executes with no sandbox. JFrog (Jan
  2026) and The Register (Jan 2026) documented that 23% of top-1,000 HuggingFace
  models were compromised at some point; NeMo-format configs were a primary
  carrier alongside malicious pickle `.pt` files. The attack requires no Python
  import — the YAML config is the entire payload.
  **aigis takeaway:** Detect config strings containing `_target_:` pointing to
  dangerous OS/exec/subprocess/pickle classes.
  - Source: <https://www.theregister.com/2026/01/13/ai_python_library_bugs_allow/>
  - Source: <https://jfrog.com/blog/data-scientists-targeted-by-malicious-hugging-face-ml-models-with-silent-backdoor/>

- **LangGraph CVE-2025-67644 — SQL injection in checkpoint filters (CVSS 7.3).**
  LangGraph's SQLite checkpoint backend does not sanitize metadata filter keys,
  allowing SQL metacharacters to escape the query context. An attacker who
  controls a LangGraph metadata filter input can read or delete checkpoint rows.
  **aigis takeaway:** Existing SQL_INJECTION_PATTERNS partially cover this; a
  LangGraph-specific sub-rule could improve signal-to-noise (pending idea).
  - Source: <https://thehackernews.com/2026/03/langchain-langgraph-flaws-expose-files.html>

- **Typosquatting campaigns targeting AI/ML packages (300+ packages, 2025-2026).**
  RH-ISAC documented automated campaigns deploying 300+ typosquatted packages
  mimicking `transformers`, `requests`, `langchain`, `llama-index`, etc. Payloads
  include zgRAT deployed via pip install hooks. Pip's case-insensitivity and
  hyphen/underscore equivalence are exploited to create nearly indistinguishable
  names.  Endor Labs (2025) also found that 44–49% of AI-suggested package
  versions contain known CVEs.
  **aigis takeaway:** A typosquatting heuristic (Levenshtein distance against a
  known-good AI package list) would require runtime dict lookup — feasible but
  needs careful list maintenance. Saved as a pending idea.
  - Source: <https://rhisac.org/threat-intelligence/typosquatting-campaign-targets-python-developers-with-hundreds-of-malicious-libraries/>

- **LoRA / fine-tuning adapter backdoors (MasqLoRA, arxiv:2602.21977).**
  Malicious LoRA adapters contain hidden backdoors that activate on specific
  trigger phrases while behaving normally otherwise. MasqLoRA (Feb 2026) achieves
  99.8% attack success rate via cross-modal mapping.  156% surge in supply chain
  attacks (2025 vs 2024) attributed partly to adapter marketplaces. Detection is
  hard purely by regex — requires weight-magnitude heuristics.
  **aigis takeaway:** Flagging adapter downloads from zero-history accounts is a
  documentation/policy recommendation; not a viable input-filter rule. Saved as
  a pending idea.
  - Source: <https://arxiv.org/abs/2602.21977>

---

## Candidate hardenings

1. **Extend `sc_compromised_pkg_version`** — add torch 2.5.0–2.5.1 (CVE-2025-32434,
   CVSS 9.3) to the known-bad version list. Very high precision; exact version
   strings only.

2. **New `sc_langchain_deserialization`** (score 70) — detect `langchain_core.loads(`
   or `langchain.loads(` calls and JSON with `"lc":"1"` deserialization marker
   (CVE-2025-68664, CVSS 9.3).

3. **New `sc_hydra_target_rce`** (score 75) — detect YAML config strings with
   `_target_: os.system / subprocess.* / builtins.exec / importlib.import_module`
   (CVE-2025-23304, NeMo/Hydra model-config RCE).

4. **Pending — typosquatting heuristic** — Levenshtein distance against a
   known-good AI package whitelist. Requires maintained whitelist; deferred.

5. **Pending — LoRA adapter policy doc** — Guidance on verifying LoRA adapters
   from Hugging Face before loading. No regex rule viable; deferred as docs.
