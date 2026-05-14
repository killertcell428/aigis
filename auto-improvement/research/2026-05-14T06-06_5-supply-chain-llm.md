# Supply Chain LLM — Research Note (Third Pass)

**Cycle:** 5 (third pass) · **Domain:** supply-chain-llm · **UTC:** 2026-05-14T06-06

Prior coverage:
- 2026-05-08T12-10: LiteLLM/TeamPCP, slopsquatting, malicious LLM API routers, pickle deserialization, skill ecosystem poisoning
- 2026-05-11T00-00: LangChain CVE-2025-68664, PyTorch CVE-2025-32434, NeMo/Hydra CVE-2025-23304, typosquatting, LoRA backdoors

This pass focuses on the **Mini Shai-Hulud coordinated supply chain campaign (May 2026)** and the
**PyTorch Lightning targeted compromise (April 2026)**, both of which specifically target AI/ML
developers and their toolchains.

---

## Findings

- **Mini Shai-Hulud campaign — coordinated npm + PyPI attack on AI packages (May 11-12, 2026).**
  TeamPCP launched a coordinated, automated attack compromising 172 packages across 403 malicious
  versions on npm and PyPI in a 48-hour window. AI/ML packages directly affected on PyPI include:
  `mistralai==2.4.6` (stealer injected into `mistralai/client/__init__.py` — downloads a secondary
  payload disguised as `transformers.pyz` from a remote IP and executes it silently on Linux on
  import) and `guardrails-ai==0.10.1` (same payload delivery mechanism). The npm side hit
  `@tanstack`, `@uipath`, `@mistralai`, and `@opensearch-project` scopes. PyPI quarantined the
  packages within hours, but any environment that ran `pip install` during the window was compromised.
  **aigis takeaway:** Add `mistralai==2.4.6` and `guardrails-ai==0.10.1` to the
  `sc_compromised_pkg_version` known-bad version list.
  - Source: <https://thehackernews.com/2026/05/mini-shai-hulud-worm-compromises.html>
  - Source: <https://www.bankinfosecurity.com/mass-supply-chain-attack-slams-npm-pypi-hits-mistral-ai-a-31672>

- **Mini Shai-Hulud exfiltration channels and IOCs.**
  The stealer payload exfiltrates stolen credentials (GitHub tokens, cloud credentials, SSH keys,
  Kubernetes configs, `.env` files, 1Password/Bitwarden password vaults) via three redundant
  channels: (1) hardcoded IP `83.142.209[.]194`, (2) Session messenger network via `*.getsession.org`
  using a fixed recipient ID, and (3) GitHub API dead drops where compromised tokens are used to
  create repos with the marker description "Shai-Hulud: Here We Go Again". The payload only runs on
  Linux and exits if the system locale is Russian or if fewer than four CPUs are detected (geofencing).
  **aigis takeaway:** The specific exfil IP (`83.142.209.194`) and the disguised payload name
  (`transformers.pyz` — chosen to blend in with the legitimate `transformers` library) are high-
  precision IOC signals in agent inputs or outputs.
  - Source: <https://hackread.com/teampcp-mini-shai-hulud-worm-npm-pypi-packages/>
  - Source: <https://www.kodemsecurity.com/resources/mini-shai-hulud-strikes-pytorch-lightning-and-intercom-client-inside-the-cross-ecosystem-supply-chain-attack>

- **PyTorch Lightning supply chain attack — IDE persistence via Claude Code hooks (April 30, 2026).**
  Versions `lightning==2.6.2` and `lightning==2.6.3` were published to PyPI on April 30, 2026 with
  an injected `_runtime/` directory. On import, the malicious code executed automatically and:
  (1) wrote a `SessionStart` hook entry in `.claude/settings.json` pointing to
  `node .vscode/setup.mjs` — achieving persistence in every Claude Code session opened in that
  project; (2) wrote a parallel `runOn: folderOpen` task in `.vscode/tasks.json` pointing to
  `node .claude/setup.mjs` for VS Code persistence. The two hooks cross-reference each other so
  either IDE triggers the payload. The malicious versions were live for 42 minutes before PyPI
  quarantined them (safe version: `lightning==2.6.1`). Commit messages used the prefix
  `EveryBoiWeBuildIsAWormyBoi` as a campaign marker.
  **aigis takeaway:** (1) Add `lightning==2.6.2` and `lightning==2.6.3` to
  `sc_compromised_pkg_version`. (2) Add a new rule detecting attempts to write malicious hooks
  to `.claude/settings.json` or `.vscode/tasks.json` — a novel IDE-persistence vector that agents
  could be tricked into propagating via indirect prompt injection.
  - Source: <https://thehackernews.com/2026/04/pytorch-lightning-compromised-in-pypi.html>
  - Source: <https://lightning.ai/blog/pytorch-lightning-supply-chain-attack>
  - Source: <https://socket.dev/blog/lightning-pypi-package-compromised>

- **TanStack GitHub Actions OIDC token extraction technique.**
  TanStack traced the Mini Shai-Hulud compromise to a chained GitHub Actions attack: attackers
  abused the `pull_request_target` trigger to gain runner access, poisoned the Actions cache,
  and extracted OIDC tokens from `/proc/*/mem` (runner process memory) to impersonate TanStack's
  legitimate release pipeline. The packages were published using TanStack's own trusted OIDC
  identity — bypassing PyPI's Trusted Publisher verification entirely. This technique (process
  memory extraction + OIDC impersonation) is distinct from credential theft and not blocked by
  MFA or Trusted Publisher.
  **aigis takeaway:** OIDC-based supply chain compromise cannot be detected at package-install
  time through version matching alone — reinforces the need for hash-pinning (`--require-hashes`)
  rather than version pinning only. Documentation candidate.
  - Source: <https://snyk.io/blog/tanstack-npm-packages-compromised/>
  - Source: <https://www.csoonline.com/article/4170284/mistral-ai-sdk-tanstack-router-hit-in-npm-software-supply-chain-attack.html>

- **`transformers.pyz` — disguised secondary payload delivery pattern.**
  The Mini Shai-Hulud payload downloads a file named `transformers.pyz` from the attacker's server
  to `/tmp/`. The name mimics the ubiquitous Hugging Face `transformers` library to avoid suspicion
  in process listings and audit logs. PYZ (Python zip application) format allows embedding a full
  Python application as a single portable archive; the file executes with `python transformers.pyz`
  or via `exec`. This naming-deception technique for secondary payloads (choosing filenames that
  mirror common, trusted libraries) was also used in the original LiteLLM attack (`litellm_init.pth`
  mimicking normal `.pth` files).
  **aigis takeaway:** Detect agent outputs that suggest downloading `.pyz` files to `/tmp/` or that
  reference `transformers.pyz` explicitly — a very high-precision IOC.
  - Source: <https://hackread.com/teampcp-mini-shai-hulud-worm-npm-pypi-packages/>

- **Supply chain attack scope continues to widen — 400+ packages in a single campaign.**
  Across all Mini Shai-Hulud waves (original + this wave), TeamPCP has now compromised over 400
  npm and PyPI packages. The Graphalgo campaign (Lazarus Group) contributed 234 additional malicious
  packages in H1 2025. The attack surface for AI/ML developers is especially large because AI
  projects tend to have deep dependency trees (transformers, torch, langchain, litellm, guardrails,
  lightning) and many are deployed in CI/CD environments with broad cloud credential access —
  exactly the credentials the stealers target.
  **aigis takeaway:** Complements the existing `sc_compromised_pkg_version` rule (extend with new
  known-bad versions from this campaign). No single regex can provide comprehensive coverage; the
  version-pinning approach needs to be paired with hash verification guidance.
  - Source: <https://securityboulevard.com/2026/05/mini-shai-hulud-is-back-172-npm-and-pypi-packages-compromised-in-latest-wave/>

---

## Candidate hardenings

1. **Extend `sc_compromised_pkg_version`** — add Mini Shai-Hulud and PyTorch Lightning compromised
   versions: `mistralai==2.4.6`, `guardrails[-_]ai==0.10.1`, `lightning==2.6.[23]`.
   Very high precision; exact version strings only, no false positives.

2. **New `sc_ide_hook_tamper`** (score 75, input/output filter) — detect attempts to write
   malicious `SessionStart` hooks into `.claude/settings.json` or `runOn: folderOpen` tasks into
   `.vscode/tasks.json`. Codifies the PyTorch Lightning IDE-persistence attack vector, where a
   compromised package silently installed a backdoor hook that executed on every IDE session open.
   An AI agent prompted via indirect injection to "update settings" could propagate the same vector.

3. **Pending — `--require-hashes` guidance document** — The OIDC impersonation technique makes
   version-only pinning insufficient. A documentation hardening guide on hash-pinning (`pip install
   --require-hashes -r requirements.txt`) and Sigstore attestation verification would be valuable
   but is a documentation-only change (deferred to a documentation cycle).

4. **Pending — `transformers.pyz` / `.pyz` secondary payload detector** — A rule detecting agent
   outputs that suggest downloading `.pyz` files to `/tmp/` would catch the Mini Shai-Hulud
   secondary payload naming pattern. However, `.pyz` is a legitimate Python format and context
   sensitivity makes a precise, low-false-positive rule hard. Deferred.
