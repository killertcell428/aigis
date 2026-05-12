# Aigis Assurance Case

> Last updated: 2026-05-12 — covers the v1.0.x release line.
>
> This document is the **threat model, trust boundary, and security
> design rationale** for the Aigis library. It exists to satisfy the
> OpenSSF Best Practices Silver tier `assurance_case` criterion and to
> give security reviewers a single entry point into how the project
> argues that it is fit for purpose.

---

## 1. Claim

> **Aigis reduces — but does not eliminate — the risk of prompt
> injection, data exfiltration, and policy-violating outputs in LLM
> applications, by interposing a deterministic detection-and-enforcement
> layer between untrusted inputs/outputs and the model.**

Sub-claims:

1. **C1 — Detection coverage.** Aigis flags a documented set of attack
   classes (OWASP LLM Top 10 LLM01–LLM10, MITRE ATLAS techniques
   AML.T0050/T0051/T0054/T0055, CSA AI Controls A.4.1/A.5.x) with
   measured ASR baselines in the published benchmark.
2. **C2 — Defense in depth.** Aigis is *one* layer; it is designed to
   be combined with input validation, output sanitization, and least
   privilege at the surrounding application.
3. **C3 — Safe failure.** When Aigis fails (false negative, parser
   crash, dependency error) the calling application can fall back to
   "deny by default" via the documented `Guard.strict_mode` and the
   activity stream's `error` event.

---

## 2. Operational Environment & Trust Boundaries

```
┌──────────────────────────────────────────────────────────────────────┐
│  Untrusted zone                                                       │
│   • End-user prompts                                                  │
│   • Tool / MCP responses                                              │
│   • RAG documents                                                     │
│   • Web pages, files, third-party APIs                                │
└────────────────────────┬─────────────────────────────────────────────┘
                         │  (trust boundary T1: data crossing
                         │   from untrusted source → host app)
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Host application (developer-controlled)                              │
│   • Calls `Guard.scan(...)` / `scan_output(...)` / `scan_mcp_tool()`  │
│   • Owns secret keys, system prompt, tool registry                    │
└────────────────────────┬─────────────────────────────────────────────┘
                         │  (trust boundary T2: process / library
                         │   call into Aigis)
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Aigis library (in-process, stdlib only)                              │
│   L1 Regex   L2 Semantic   L3 Decoding                                │
│   L4 CaMeL   L5 AEP         L6 Spec Verifier                          │
│   → returns ScanResult (allow / flag / block) + remediation hint      │
└────────────────────────┬─────────────────────────────────────────────┘
                         │  (trust boundary T3: outbound to LLM
                         │   provider — out of scope for Aigis)
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  LLM provider (Anthropic / OpenAI / self-hosted)                      │
└──────────────────────────────────────────────────────────────────────┘
```

- **T1 is the primary defended boundary.** Everything crossing T1 is
  assumed hostile until scanned.
- **T2 is a same-process trust boundary.** Aigis runs as a library, not
  a service, so the host process can read/modify Aigis state. We do
  *not* defend against a malicious host.
- **T3 is out of scope.** Network transport security, provider auth,
  and provider-side moderation are the host application's
  responsibility. Aigis ships no network code in the core.

---

## 3. Adversary Model

| Adversary | Capabilities | In scope |
| --- | --- | --- |
| **A1: External end-user** | Crafts any prompt, including obfuscated, multilingual, encoded variants | ✅ primary |
| **A2: Compromised content source** | Controls RAG documents, web pages, tool outputs returned to the agent (indirect injection) | ✅ primary |
| **A3: Malicious MCP server** | Returns a poisoned tool definition or tool response | ✅ |
| **A4: Network attacker (passive)** | Observes traffic between host and LLM | ❌ delegated to TLS at host |
| **A5: Network attacker (active)** | MITMs host↔LLM | ❌ delegated to host TLS verification |
| **A6: Compromised host process** | Runs in the same process as Aigis | ❌ out of scope (T2 collapsed) |
| **A7: Compromised maintainer / supply chain** | Publishes a poisoned `pyaigis` release | Partial — mitigated by PyPI Trusted Publishing (OIDC), Sigstore attestations, branch protection, DCO |

---

## 4. Top Threats and Mitigations

| ID | Threat | Layer(s) that mitigate | Residual risk |
| --- | --- | --- | --- |
| **TH-01** | Direct prompt injection ("ignore previous instructions…") | L1 regex (165+ patterns × 4 langs), L2 semantic similarity | Novel paraphrases not in pattern set; tracked via auto-improvement loop |
| **TH-02** | Indirect prompt injection via RAG/tool output | `scan_rag_context()`, `scan_mcp_tool()`, L4 CaMeL taint tracking | Compositional attacks across multiple documents |
| **TH-03** | Encoded payloads (Base64, hex, ROT13, Unicode tag block, fullwidth) | L3 active decoding + rescan; cycle-7 detectors for Unicode tag/fullwidth Latin | Novel encodings not in decoder set |
| **TH-04** | Multilingual evasion (EN→JA→KO→ZH) | L1 patterns ship in 4 languages with NFKC + confusable normalization | Low-resource languages outside the four supported |
| **TH-05** | Data exfiltration via tool calls | L4 CaMeL capability tokens, `no_exfil` built-in safety spec | Spec must be enabled by host |
| **TH-06** | PII leakage in LLM output | `scan_output()` PII patterns, `pii_guard` spec | Regex coverage is best-effort, not exhaustive |
| **TH-07** | Policy bypass via jailbreak persona (DAN, AIM, etc.) | L1 jailbreak patterns, L2 similarity, evasion-obfuscation cycle detectors | Novel personas; mitigated by ongoing auto-improvement loop |
| **TH-08** | Supply chain compromise of `pyaigis` itself | PyPI Trusted Publishing (OIDC), pinned action SHAs, Dependabot, CodeQL, Scorecard, signed releases (Sigstore) | Long-tail transitive deps; mitigated by zero-runtime-dependency core |
| **TH-09** | Crypto misuse | No bespoke crypto in core; uses Python `hashlib` (SHA-256) and `PyJWT` with explicit algorithm allowlist | None known |
| **TH-10** | Denial of service via pathological input (ReDoS, huge inputs) | Bounded-time regex patterns, input length cap, `pytest --timeout` in CI | Adversarial regex inputs against new patterns; covered by regression tests |

---

## 5. Secure Design Principles (mapping)

This project explicitly implements the following classical secure-design
principles. Citations below point to the file or class where the
principle is realized.

| Principle | Realization in Aigis |
| --- | --- |
| **Economy of mechanism** | Core has *zero runtime dependencies* — Python stdlib only. The detection engine is a small pure-function pipeline. (`aigis/scanner.py`) |
| **Fail-safe defaults** | `Guard(strict=True)` blocks on any error or uncertain match. The default `ScanResult` action is `block` when severity ≥ `high`. |
| **Complete mediation** | All inputs/outputs/RAG/tool definitions pass through one of `scan*` entry points; no bypass path. Documented in `ARCHITECTURE.md`. |
| **Open design** | All patterns, weights, and decoder rules are open source. Security does not depend on secrecy of the rule set. |
| **Separation of privilege** | L4 CaMeL separates *control flow* (from trusted system prompt) and *data flow* (from untrusted tools/RAG). |
| **Least privilege** | Capability tokens (CaMeL) require explicit grant; default-deny on tool execution. |
| **Least common mechanism** | Library is in-process and stateless per call. No shared global state, no daemon, no shared cache between tenants. |
| **Psychological acceptability** | Single-import API: `from aigis import Guard; Guard().scan(text)`. Three-line quick-start in `README.md`. |
| **Defense in depth** | Six independent detection layers (L1–L6); failure of any single layer is not catastrophic. |
| **Work factor** | Multilingual + decoded + semantic detection forces an attacker to bypass *all* layers across *all* languages. |
| **Compromise recording** | Activity stream emits structured events (`local`, `global`, `alert`); pluggable sinks let the host ship them to SIEM. |

---

## 6. Assumptions

The argument above relies on these assumptions. If any is invalid in
your deployment, the residual risk increases.

1. **A-RUNTIME** — The host runs a supported Python interpreter
   (3.11+) without bytecode tampering.
2. **A-DEPS** — The published `pyaigis` wheel matches what
   PyPI/Sigstore attest. Verify via `pip install --require-hashes` or
   the published Sigstore bundle.
3. **A-HOST** — The host application correctly:
   - calls Aigis on every untrusted input/output,
   - honors `ScanResult.action == "block"` by refusing to send the
     payload to the LLM, and
   - does not paste raw `Guard` internals into the prompt itself.
4. **A-TLS** — Network traffic between the host and the LLM provider
   is TLS 1.2+ with certificate verification enabled. (Aigis ships no
   network code, so we do not verify this.)
5. **A-KEYS** — LLM API keys live in environment variables / a secret
   manager, not in source. See `docs/access_continuity.md`.

---

## 7. Evidence

| Claim | Evidence |
| --- | --- |
| Detection coverage measured | `docs/compliance/OWASP_LLM_TOP10_COVERAGE.md`, `docs/compliance/MITRE_ATLAS_COVERAGE.md`, benchmark results in release notes |
| Compliance mapping | `docs/compliance/NIST_AI_RMF_MAPPING.md`, `docs/compliance/CSA_STAR_AI_SELF_ASSESSMENT.md` |
| MCP-specific architecture | `docs/compliance/MCP_SECURITY_ARCHITECTURE.md` |
| Continuous regression | `.github/workflows/ci.yml` (940+ tests, multi-OS matrix), `--cov-fail-under=68` ratchet |
| Supply-chain controls | `.github/workflows/codeql.yml`, `.github/workflows/scorecard.yml`, `.github/dependabot.yml`, PyPI Trusted Publishing in `release.yml` |
| Vulnerability response | `SECURITY.md` (≤72 h ack, ≤60 d fix for high/critical, ≤90 d disclosure) |
| Continuity & key custody | `docs/access_continuity.md` |
| Threat-model maintenance | This document; reviewed on every minor release |

---

## 8. Review Cadence

- **On every minor release** (`v1.x.0`) — refresh §4 (Top Threats) and
  §7 (Evidence) tables.
- **On every patch release** — verify §6 assumptions still hold; no
  edits needed if unchanged.
- **Annually** — full re-read of §1–§5; update adversary model with
  any new attack classes observed in the wild.
- **On any high/critical advisory** — add an entry to §4 and link the
  advisory.
