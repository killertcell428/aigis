# Supply Chain LLM — Research Note

**Cycle:** 5 · **Domain:** supply-chain-llm · **UTC:** 2026-05-08T12-10

---

## Findings

- **TeamPCP / LiteLLM PyPI compromise (March 2026, critical).**
  Threat actor group TeamPCP exploited an unsanitized `pull_request_target`
  workflow in the Trivy security-scanner CI/CD pipeline to steal the
  `aqua-bot` PAT, then used it to publish `litellm==1.82.7` and
  `litellm==1.82.8` to PyPI on March 24, 2026 (live ~40 minutes before
  PyPI quarantined them). Version 1.82.8 embedded `litellm_init.pth`, a
  `.pth` file that auto-executes a credential-harvester on every Python
  interpreter start — no `import litellm` required. The payload harvested
  SSH keys, `.env` files, AWS/GCP/Azure credentials, Kubernetes configs,
  shell history, and env vars, encrypted them with a hardcoded 4096-bit
  RSA key, and exfiltrated them to `https://models.litellm.cloud/`.
  **aigis takeaway:** Add litellm 1.82.7-1.82.8 to `KNOWN_VULNERABLE` and
  add a detector for the `models.litellm.cloud` exfil domain.
  - Source: <https://thehackernews.com/2026/03/teampcp-backdoors-litellm-versions.html>
  - Source: <https://securitylabs.datadoghq.com/articles/litellm-compromised-pypi-teampcp-supply-chain-campaign/>
  - Source: <https://github.com/BerriAI/litellm/issues/24512>

- **Slopsquatting — LLM-hallucinated package names weaponized (2026).**
  Researchers at Socket.dev found that ~20% of packages recommended by LLM
  coding assistants do not exist on PyPI/npm; 58% of hallucinated names are
  *repeatable* (same prompt → same fake name across 10 runs). Attackers
  register these hallucinated names and publish malicious packages. In
  January 2026, Aikido Security researcher Charlie Eriksen registered
  `react-codeshift` (hallucinated by an LLM) and it appeared in 237 GitHub
  repos. North Korea's Lazarus Group (Graphalgo campaign) attributed 234
  unique malware packages to PyPI/npm in H1 2025.
  **aigis takeaway:** Add a detector for `pip install` commands referencing
  known-compromised AI package versions; flag direct references to known
  supply-chain exfil domains.
  - Source: <https://socket.dev/blog/slopsquatting-how-ai-hallucinations-are-fueling-a-new-class-of-supply-chain-attacks>
  - Source: <https://www.aikido.dev/blog/slopsquatting-ai-package-hallucination-attacks>

- **Malicious LLM API routers / intermediary attacks (arxiv:2604.08407).**
  April 2026 paper studied 428 third-party LLM API routers (proxies that
  forward tool-call JSON between client and upstream model). Found 9 actively
  injecting malicious payloads (2 with adaptive evasion), 17 touching
  researcher-owned AWS canary credentials, and 1 draining ETH. Defines two
  core attack classes: AC-1 (payload injection) and AC-2 (secret
  exfiltration). Routers have full plaintext access to every in-flight
  JSON payload; no provider enforces cryptographic integrity.
  **aigis takeaway:** Detect references to unofficial/suspicious LLM API
  gateway domains in agent inputs and outputs.
  - Source: <https://arxiv.org/abs/2604.08407>

- **Pickle deserialization attacks on Hugging Face models (2024-2026).**
  JFrog discovered 100+ malicious ML models on Hugging Face using
  `__reduce__` pickle method to execute arbitrary code on `torch.load()`.
  By early 2025 >3,300 of 400K scanned models were found to contain
  rogue-code payloads. Feb 2025 research documented "nullifAI" technique —
  evading Hugging Face's PickleScan by exploiting broken pickle framing.
  SafeTensors was introduced as a safe alternative, yet `torch.load()`
  without `weights_only=True` remains the most common unsafe loading pattern.
  **aigis takeaway:** Flag unsafe `torch.load()` calls (without
  `weights_only=True`) and raw `pickle.loads(` on model data in LLM outputs.
  - Source: <https://jfrog.com/blog/data-scientists-targeted-by-malicious-hugging-face-ml-models-with-silent-backdoor/>
  - Source: <https://thehackernews.com/2025/02/malicious-ml-models-found-on-hugging.html>
  - Source: <https://arxiv.org/abs/2602.19818>

- **Supply-chain poisoning of LLM coding agent skill ecosystems (arxiv:2604.03081).**
  April 2026 paper describes how attackers plant backdoored "skills" (tools /
  function libraries) in AI agent marketplaces. The poisoned skill executes
  normally 99% of the time, activating only when a trigger phrase appears
  in the conversation — making automated detection difficult.
  **aigis takeaway:** The MCP tool-tampering patterns already in aigis cover
  the definition-hash side; the skill ecosystem angle is a future pending
  investigation.
  - Source: <https://arxiv.org/abs/2604.03081>

- **SoK: LLM supply chain vulnerability taxonomy (arxiv:2502.12497).**
  Comprehensive survey classifying LLM supply chain threats across training
  data poisoning, model-weight tampering, fine-tuning backdoors, plugin
  dependency abuse, and deployment-time attacks. Identifies that 97% of AI
  projects contain at least one vulnerable dependency, and that supply chain
  attacks have increased 3× year-over-year.
  **aigis takeaway:** The taxonomy confirms the rule-based hardenings above
  (package version checks, exfil domain detection, unsafe load detection)
  cover the highest-frequency attack vectors in the deployment tier.
  - Source: <https://arxiv.org/abs/2502.12497>

---

## Candidate hardenings

1. **`KNOWN_VULNERABLE` update** (`aigis/supply_chain/verify.py`): Add litellm
   1.82.7–1.82.8 (TeamPCP, March 2026, critical) to the built-in known-bad
   version database.

2. **`SUPPLY_CHAIN_PATTERNS`** (`aigis/filters/patterns.py`): Three new input
   detectors:
   - `sc_unofficial_llm_router` (score 75) — detects `models.litellm.cloud`
     and similar unofficial LLM API proxy/relay domains (AC-2 exfil channel
     from arxiv:2604.08407 and TeamPCP incident).
   - `sc_pickle_unsafe_model_load` (score 55) — detects `torch.load()` without
     `weights_only=True` and raw `pickle.loads(` on model data (primary vector
     for Hugging Face malicious model payloads).
   - `sc_compromised_pkg_version` (score 80) — detects `pip install` commands
     referencing exact known-compromised version strings (litellm 1.82.7/8,
     1.56.0–3; ultralytics 8.3.41–42).
