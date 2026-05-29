# Cryptographic and formal-methods primitives for AI/LLM agent security

The thesis: detection alone has a ceiling, but the cryptographic primitives that would actually shift that ceiling are at very different states of maturity. Some are deployable in 2026 with modest effort; others are research papers with two-orders-of-magnitude overhead.

## 1. Trusted Execution Environments

**CPU TEEs.** Intel SGX is end-of-life on client CPUs and surviving in a reduced form on Xeon scalable; Intel TDX is the successor and provides VM-level isolation rather than enclave-level. AMD SEV-SNP is the production-deployed equivalent. ARM provides TrustZone (mobile, mature) and CCA (Confidential Compute Architecture, server, shipping in Neoverse V3/Cobalt). RISC-V Keystone is research. Apple's Secure Enclave is a co-processor for key custody.

**Cloud-vendor wrappers.** AWS Nitro Enclaves are the most pragmatic TEE in production: VM-isolated, no SGX-style side-channel surface, simple attestation document signed by AWS root. Azure Confidential VMs use SEV-SNP or TDX. GCP Confidential Space adds an attested workload identity. None of these protect against the cloud vendor itself.

**GPU TEEs — the actual unblock for LLMs.** NVIDIA Confidential Computing is supported on H100, H200, B200 (Blackwell), and GB200. The on-die Confidential Compute Engine AES-256-GCM-encrypts every HBM write; Blackwell adds encrypted NVLink and PCIe 5.0. Throughput penalty measured at 4–8% on H100 inference, diminishing with batch size ([arxiv:2509.18886](https://www.arxiv.org/pdf/2509.18886)).

**What this actually protects, for LLMs.**
- Model weights at rest and in HBM: yes.
- System prompts and KV-cache in HBM: yes.
- A malicious tenant on the same node: yes.
- Side channels (cache, power, EM): mostly no — see §8.
- The cloud provider with hardware access: no, by design.

**Apple Private Cloud Compute** is the most articulated commercial threat model. Devices wrap request keys only to public keys of nodes whose attested measurements match a build in the public transparency log; Apple commits to publishing every production PCC image for inspection. Closest thing to "cryptographic deployment of an LLM" as of 2026.

Anthropic and OpenAI have made limited public statements: Anthropic operates on AWS and references Nitro Enclaves in some compliance contexts; OpenAI's "ZDR" is policy, not cryptography. Neither has shipped attested confidential inference equivalent to PCC.

## 2. Zero-Knowledge Proofs

**Primitives.** zkSNARKs (Groth16, PLONK, HyperPlonk) give short proofs and small verifier cost at the price of a trusted setup and expensive prover. zkSTARKs (post-quantum, transparent setup) trade larger proofs for no setup. Folding schemes (Nova, HyperNova) and lookup arguments are the 2024–2026 plumbing.

**State of zkML, 2025–2026.** EZKL (open-source, Halo2-based) is the lingua franca for proving small ONNX models. Modulus Labs and Giza target on-chain inference up to ~18M parameters. Lagrange's DeepProve-1 (2025) is the first system to prove a full GPT-2 (124M) forward pass; reported 50–150× faster than EZKL. zkPyTorch (March 2025) compiles PyTorch graphs directly to ZK circuits and proves VGG-16 (138M) in ~2.2s. zkLLM and NANOZK ([arxiv:2603.18046](https://arxiv.org/pdf/2603.18046)) explore layerwise proofs.

**What can be proven.** A specific model `M` with specific weights `W` produced output `y` from input `x`. The verifier learns only `(commit(W), commit(x), y)` and a proof. Exactly the primitive needed for "verifiable inference."

**What cannot be proven.** That the model is *safe*, *aligned*, or *not jailbroken*. ZK proves a computation matches a circuit; it does not encode semantic properties. Also: GPT-2 is ~3 orders of magnitude smaller than current frontier models.

## 3. MPC and Homomorphic Encryption

**MPC for inference.** 2-party and 3-party protocols (CrypTen, MP-SPDZ, Cheetah, Iron, Bumblebee) have been demonstrated for BERT-scale models with latencies of seconds to tens of seconds per inference. State of the art for transformer MPC sits around 30–100× slowdown vs plaintext for sub-billion-param models.

**FHE for inference.** ZAMA's Concrete-ML v1.7 ships an LLM example that runs GPT-2 token generation in ~11s on H100 GPU. A LLAMA-1B FHE prototype exchanges ~18 MB per token. For frontier-scale models, FHE is still firmly research.

**Verdict.** MPC for narrow, small models in regulated settings (healthcare, finance) is feasible today. FHE for LLM-scale is not. **For Aigis, neither MPC nor FHE is the right v2 primitive** — they protect *inputs* from the model provider, which is orthogonal to Aigis's threat model.

## 4. Cryptographic provenance and attestation

**Mature primitives, deployable now.**
- **Sigstore / cosign** for keyless signing of artifacts (containers, binaries, models). NVIDIA NGC began signing models with Sigstore in July 2025; Hugging Face has experimental support.
- **SLSA** (Supply-chain Levels for Software Artifacts).
- **In-toto / ITE-6** is the envelope format that carries provenance claims.
- **TPM/DICE** provide hardware-rooted device identity and measured boot.
- **C2PA** signs media manifests. Manifest format is content-agnostic and could carry signed system prompts as assertions.

**This is the area where Aigis can ship something cryptographic in 2026 with minimal R&D.**

## 5. Formal verification

**What works at LLM scale.** Essentially nothing on the weights themselves. Formal methods cannot verify semantic safety properties of a neural network beyond toy robustness bounds.

**What works around LLMs.**
- seL4-style verified kernels for sandboxing.
- Verus, F*, Lean, Coq for verifying the *guardrail code itself* — Aigis's detection pipeline, policy engine, signature-verification path. Realistic and high-leverage.
- IFC type systems for taint-tracking from untrusted inputs to dangerous tool calls. Closest thing to a "formal model of prompt injection" — see the CaMeL design pattern ([arxiv:2506.08837](https://arxiv.org/pdf/2506.08837)).

## 6. Concrete proposals for Aigis v2

### Proposal A — Signed prompt and tool-descriptor provenance (Sigstore + in-toto)

Every system prompt, tool description, and MCP server manifest is signed by its author using Sigstore (keyless OIDC) and wrapped in an in-toto attestation. Aigis ships a verifier that:

1. Refuses to load an unsigned tool descriptor (configurable).
2. Records the signing identity in the audit log alongside every tool call.
3. Pins expected signers per project via an `aigis.lock`-style file.

**Attack model defeated.** MCP rug-pull (vendor silently swaps `read_file`'s description). Modified descriptor fails signature verification.
**Feasibility today.** High. 2–4 engineer-weeks for MVP. **Ship in v2.**

### Proposal B — TEE-enclaved system prompt + capability tokens (Nitro Enclaves)

System prompts and capability tokens live only inside an AWS Nitro Enclave. The orchestrator process can request inference via a typed RPC but never sees prompt plaintext.

**Attack model defeated.** Compromised orchestrator process. Memory scraping. Lateral movement from a co-tenant.
**Feasibility today.** Medium. 1–2 quarters. Adds AWS lock-in unless paired with TDX/SEV-SNP equivalents. **Prototype in v2, ship in v2.1.**

### Proposal C — ZK-attested tool execution

MCP servers produce a ZK proof that `output = f(schema, input)` for a declared schema-conformant `f`.

**Feasibility today.** Low for general `f`. **Do not prototype in v2.** Revisit when general-purpose ZK-VMs (RISC0, SP1, Jolt) hit sub-10× overhead.

### Proposal D — Per-session prompt salt + rule-selection seed (asymmetric defense)

Aigis generates a per-session random `salt` and a per-session `rule_seed` from a master key. Detection rules incorporate the salt (so an attacker probing a public Aigis can't deterministically reproduce the rule set they will face in production); the rule_seed selects a random subset of equivalent detectors. The algorithm is fully public; only the keys are secret. Stackelberg-style: the defender commits to a distribution.

**Attack model defeated.** Offline jailbreak optimization against a known detector set. "Read the code, find the gap" attacks.
**Feasibility today.** High. 1–2 engineer-weeks. **Ship in v2.** This is the Kerckhoffs answer to the open-source detector problem.

## 7. The asymmetry argument — what's the "key" in AI security?

| Secret | Role | Maturity |
|---|---|---|
| Signing key (developer/vendor) | Authorizes prompts, tools, models | Production |
| Per-session prompt salt | Defeats offline jailbreak search | Trivial to deploy |
| Per-session rule-selection seed | Randomized defender strategy | Trivial to deploy |
| TEE attestation key (hardware root) | Proves enclave identity | Production (Nitro), maturing (NVIDIA CC) |
| ZK proving/verifying key pair | Attests inference or tool execution | Research for LLM-scale |
| HE secret key | Hides inputs from model | Research for LLM-scale |
| C2PA manifest signing key | Output provenance | Production for media, adaptable |

The two underused ones are the **per-session salt** and **rule-selection seed**. They cost nothing and meaningfully change the attacker's economics from "find one bypass" to "find a bypass that works across the salt distribution."

## 8. Honest critique

- **TEEs leak.** SGX has been broken repeatedly: Foreshadow, Plundervolt, SGAxe/CrossTalk, ÆPIC Leak, Downfall. Each was patched, but enclaves on shared silicon have side-channel surface. Nitro Enclaves avoid most of this by VM isolation. GPU TEEs are new enough that their side-channel surface is largely unmapped.
- **ZK is still 10–1000× overhead.** Worth it for: low-frequency, high-value attestations. Not for: per-token inference, high-throughput tool calls.
- **HE/MPC for LLM-scale is impractical.** ZAMA's GPT-2 at 11s/token is heroic engineering, but it is GPT-2. A 70B model is roughly 600× the FLOPs.
- **Formal verification of LLM weights does not exist** and is unlikely to exist for any model whose behavior is interesting. FV of *the code around* the LLM is tractable.
- **Apple PCC is the gold standard** but relies on Apple's own silicon, build pipeline, and transparency log. Replicating it for a third-party agent stack is multi-year, multi-million-dollar.

## 9. Recommended reading

1. *Confidential LLM Inference: Performance and Cost Across CPU and GPU TEEs* — [arxiv:2509.18886](https://www.arxiv.org/pdf/2509.18886). The numbers you need to make the TEE deployment decision.
2. *Apple Private Cloud Compute Security Guide* — security.apple.com/documentation/private-cloud-compute.
3. *Design Patterns for Securing LLM Agents against Prompt Injections* (CaMeL et al.) — [arxiv:2506.08837](https://arxiv.org/pdf/2506.08837).
4. *zkLLM / NANOZK* — [arxiv:2603.18046](https://arxiv.org/pdf/2603.18046).
5. *SLSA v1.0 specification* + *Sigstore: Software Signing for Everybody* (CCS '22).

## Top 3 to prototype (rank by effort × impact)

1. **Per-session salt + randomized rule selection.** ~1–2 engineer-weeks. Pure software. Immediately changes attacker economics for the open-source-detector problem. **This is the Kerckhoffs move for Aigis v2.**
2. **Sigstore + in-toto provenance for MCP tool descriptors and system prompts.** ~2–4 engineer-weeks for MVP. Mature primitives. Cryptographically defeats MCP rug-pull.
3. **Nitro Enclave companion daemon for system-prompt and capability-token custody.** ~1–2 quarters. Real cloud lock-in but ships a story for regulated buyers.

## Top 3 NOT to prototype yet (too early)

1. **FHE/MPC inference at LLM scale.** Two orders of magnitude too slow. Revisit when sub-10×-overhead transformer inference is published.
2. **General-purpose ZK-attested tool execution.** Cost asymmetric to schema validation. Revisit when zkVMs (RISC0, SP1, Jolt) hit sub-10× overhead.
3. **Formal verification of LLM behavior / "verified ML" for safety.** No path to scaling. Invest formal-methods effort in the *guardrail code* instead.
