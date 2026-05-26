# Mechanism Design as a Security Paradigm for Aigis v2

## 0. The reframing

Detection (Aigis v1) is a **classifier game**: defender picks features, attacker picks inputs, attacker moves last and wins at the limit. No amount of pattern engineering changes the structure — it's the same loss curve antivirus has been on for 30 years.

Mechanism design changes the game itself. Instead of asking *"can I tell this input is malicious?"*, you ask *"can I arrange the rules so that the malicious move is dominated by an honest one, regardless of how clever the attacker is?"* The asymmetry you want is the one blockchains discovered: cheap to verify, expensive to attack, and **the attacker pays even if they're never caught**.

For Aigis specifically, this is what survives the day someone reads `aigis/patterns/*.py` and crafts a semantic bypass: a v2 layer that doesn't depend on pattern secrecy.

## 1. Core concepts and how they map to LLM/agent security

| Concept | One-line definition | Aigis-relevant translation |
|---|---|---|
| **Incentive compatibility** | Truth-telling is a (weakly) dominant strategy | Tool calls that misrepresent their effects cost the caller more than calls that don't |
| **Strategy-proof** | Player can't gain by deviating from the mechanism's preferred input | Agent gains nothing from prompt-injecting another agent because the orchestrator routes by *capability*, not by *intent claims* |
| **VCG** | Each agent's payment = externality they impose on others | Tool calls priced by counterfactual impact on other principals' utility (rarely literal $, more often: rate-limit budget, escalation thresholds) |
| **Slashing / bonded stake** | Validators post collateral; misbehavior → forfeit | Every MCP tool call carries a slashable bond from caller (or its operator) |
| **Skin in the game** (Taleb) | Decision-makers bear downside | Whoever writes a system prompt also signs liability for its outputs |
| **Reputation** | History → trust score → access | Provenance-bound agent identity (AIP) gates which tools an agent can call |
| **Commitment schemes** | Hash now, reveal later → can't lie about what you said | Pre-execution commit to (plan, tool set, args schema); post-hoc deviations are blockable |
| **Adversarial training / GAN** | Equilibrium between attacker and defender models | Red-team agents continuously probe; new bypasses become new patterns automatically |
| **Moving target defense** | Rotate the attack surface faster than recon | Rotate prompt salts, tool ABI nonces, capability token formats |
| **Honeytokens** | Decoys whose only purpose is to fire alarms | Inject canaries into prompts/contexts; egress hit = injection succeeded |
| **Cost asymmetry** | Verifier << attacker cost | PoW / signed attestation per tool call; trivial for one user, ruinous for fuzzing |

## 2. Existing academic & industrial work (what shipped, what didn't)

**Stackelberg Security Games (Tambe et al.)** — *Did ship.* GUARDS (TSA, 400+ airports), PROTECT (USCG ports), ARMOR (LAX), IRIS (Federal Air Marshals). Defender commits first (publicly!), attacker best-responds; defender randomizes optimally. The lesson for Aigis: **publishing your rules can be safe if randomization makes the attacker's best response no better than uniform guessing**. See [Tambe lab overview](https://teamcore.seas.harvard.edu/ai-and-game-theory-public-safety-and-security/) and the [Milind chapter PDF](https://personal.ntu.edu.sg/boan/papers/Milindchapter.pdf).

**CaMeL (DeepMind, 2025)** — *Shipping in research stacks.* Capability-based dual-LLM with a Python interpreter enforcing data-flow policy. Blocks 67% of AgentDojo attacks **without retraining**. This is the closest existing instantiation of "mechanism > detection." [arxiv:2503.18813](https://arxiv.org/abs/2503.18813).

**AIP — Agent Identity Protocol (2026)** — *Draft IETF, running implementation.* Invocation-Bound Capability Tokens (IBCTs) fuse identity, attenuated authorization, and provenance into an append-only chain. Reputation derived from action receipts; 0.22 ms HTTP overhead. [arxiv:2603.24775](https://arxiv.org/abs/2603.24775), [IETF draft](https://datatracker.ietf.org/doc/draft-prakash-aip/). **This is the missing infrastructure layer Aigis can plug into.**

**Kill-Chain Canaries (2026)** — Cryptographic canary tokens tracked across 950 agent runs, 5 frontier models, 4 kill-chain stages. Conclusion: *"prompt injection is not a model-capability problem, it is a pipeline-architecture problem."* [arxiv:2603.28013](https://arxiv.org/html/2603.28013v2).

**Design Patterns for Securing LLM Agents** — Codifies action-constraining patterns; the closest thing to a "mechanism design textbook" for agent security. [arxiv:2506.08837](https://arxiv.org/html/2506.08837v3).

**Moving Target Defense for LLMs** — "Jailbreaker in Jail" (ACM MTD '23) and ADA (Kubernetes ephemeral rotation, [arxiv:2505.23805](https://arxiv.org/html/2505.23805v1)). Mostly infrastructure-level; prompt-level MTD is nascent.

**Crypto-economic primitives transferable to Aigis** — *Proof of Diligence* ([arxiv:2402.07241](https://arxiv.org/pdf/2402.07241)) and *Economic Censorship Games in Fraud Proofs* ([arxiv:2502.20334](https://arxiv.org/abs/2502.20334)) formalize how to bound rational misbehavior with stake + challenge windows.

**What hasn't shipped:** explicit VCG-style pricing for tool calls, formal prompt-injection economics modeling attacker cost. This is a research gap Aigis could occupy.

## 3. Concrete architectural proposals for Aigis v2

### 3.1 Capability tokens with slashable bond (AIP-compatible)
Every MCP tool call carries a header:

```
X-Aigis-Cap: JWS{ caller_did, tool_id, args_hash, ttl, bond_ref, parent_cap? }
```

`bond_ref` is a Merkle leaf into an operator-held bond pool. Aigis ships an `aigis.bond` module that:
1. Issues caps (orchestrator side).
2. Verifies caps (server side) before pattern checks run.
3. Emits a `SlashReceipt` when post-hoc audit (`aigis.audit.replay`) finds a cap was used to launder an injection.

Why this works: even if attacker bypasses the pattern, the cap chain names who signed off. Reputation degrades; bond burns. Closed-loop economic feedback that pattern matching alone cannot give.

### 3.2 Honeytoken canaries — `aigis.canary`
```python
canary = aigis.canary.mint(scope="system_prompt", ttl=3600)
system_prompt = canary.wrap(system_prompt)
# later, in any egress:
aigis.canary.scan(outbound_payload)  # raises CanaryLeaked → IR-13 SEV1
```
Each canary is a HMAC over (session_id, slot, nonce) — unguessable, unforgeable, and **a single hit is ground truth that exfil succeeded**. Pairs naturally with the Kill-Chain Canaries paper's empirical framework.

### 3.3 Commit-reveal plans for agents
Before any tool sequence runs, the agent must POST a `PlanCommit`:
```
commit = H(plan_dsl || nonce)
```
Tool calls during execution must each carry `(plan_idx, opening)` proving the call was in the committed plan. Mid-execution prompt injection that tries to introduce *new* tool calls fails the opening check. This directly defeats the dominant prompt-injection pattern of "hijack mid-flight."

### 3.4 Moving target prompt salting
Rotate per-session a `prompt_salt` woven into your system prompt as a required prefix on every meta-instruction. Patterns the attacker scraped from GitHub stop matching; the salt becomes a per-session shared secret between Aigis and the model. Cheap (single 16-byte token), and turns the "open source detector" problem into the "open source detector with per-session keying" problem.

### 3.5 Cost-asymmetric verification (Hashcash for tool calls)
Optional `X-Aigis-PoW: <nonce>` such that `H(call || nonce)` has `k` leading zeros. `k` is **dynamic per agent reputation**: 0 for AIP-verified high-rep agents, 18 for unknown clients. A human typing 1 req/sec doesn't notice. A fuzzing rig doing 10⁴ req/sec hits a wall.

### 3.6 Optimistic verification with fraud proofs
Tool calls execute immediately with provisional commit. A `challenge_window` (e.g., 60s) lets any auditor (could be `aigis.audit` running async) submit a `FraudProof` = (call, replay trace, violated invariant). Successful proof → slash + roll back. Borrowed wholesale from Optimistic Rollups.

### 3.7 Honeypot tools
Register decoy MCP tools (`hr_export_all_employees`, `admin_disable_filters`) that **no legitimate plan ever calls**. Any call to them is an injection. Zero false positives by construction.

## 4. The hard question — who is the designer?

Mechanism design assumes (a) a designer with authority, (b) identifiable players, (c) enforceable payments. In the open agent ecosystem all three are partial:

- **(a) Authority** holds *within* a deployment (an enterprise running its own orchestrator IS the designer for its agents) but not *across* deployments.
- **(b) Identity** is the bottleneck. Pre-AIP, MCP has no agent identity. Post-AIP, you can do real mechanism design. **Aigis should hard-couple to AIP-style identity** because every other mechanism above depends on it.
- **(c) Payment** doesn't have to be money. Slashable resources include: rate-limit budget, capability scope, reputation score, allow-list membership.

**Where the analogy holds:** within an enterprise deployment, within a federation of mutually-attested agents, within a marketplace with a curator.
**Where it breaks:** between strangers on the open internet with no shared root of trust. Here you fall back to detection (Aigis v1) plus *only* sandbox-grade isolation.

## 5. Crypto-economics: what transfers, what doesn't

**Transfers:**
- **Slashing of bonded stake** → cap tokens with operator bond.
- **Optimistic execution + fraud proofs** → execute tool, async audit, rollback on violation.
- **Fishermen / watchtowers** → third-party auditors running Aigis in replay mode against logs.
- **Challenge periods** → "high-stakes tool calls have a 30s soft commit before externalizing."

**Doesn't transfer cleanly:**
- **Global consensus** — agent ecosystems don't need or want a global ledger.
- **Token-based MEV / staking economics** — financial token markets are absent.
- **Long unbonding periods** — agent interactions are seconds, not weeks.

## 6. Honest critique — the dark side

**Sybil attacks.** Cheap identities destroy reputation systems. Mitigation: rep gated on attested compute (AIP's hardware-bound key), or on staked external resources.

**Collusion.** Two agents owned by the same attacker can fake interactions to build reputation (wash trading). Mitigation: require attestations from *disjoint* principals weighted by their *own* independently-built reputation.

**Misaligned principals.** The orchestrator's operator may *want* the agent to do shady things. Only meaningful for *cross-principal* trust.

**Wash trading / fake reputation.** Markets for high-rep agent identities will appear. Mitigation: bind reputation to **behavior under audit**, not raw call counts; sample-based replay verification.

**Mechanism gaming itself.** Honeytokens get stripped; PoW gets GPU-accelerated; cap tokens get stolen. None defeat the *paradigm* — they each force the attacker to a higher cost tier.

## 7. Recommended reading (ranked by signal)

1. **Debenedetti et al., "Defeating Prompt Injections by Design" (CaMeL), 2025** — [arxiv:2503.18813](https://arxiv.org/abs/2503.18813). Read first.
2. **Prakash, "AIP: Agent Identity Protocol," 2026** — [arxiv:2603.24775](https://arxiv.org/abs/2603.24775) + [IETF draft](https://datatracker.ietf.org/doc/draft-prakash-aip/).
3. **Beurer-Kellner et al., "Design Patterns for Securing LLM Agents," 2025** — [arxiv:2506.08837](https://arxiv.org/html/2506.08837v3).
4. **Tambe (ed.), *Security and Game Theory*, Cambridge, 2011.**
5. **Sheng et al., "Proof of Diligence," 2024** — [arxiv:2402.07241](https://arxiv.org/pdf/2402.07241).

## Top 3 concrete things to prototype (effort/impact ranked)

1. **`aigis.canary` — honeytoken module.** *Effort: 1–2 days. Impact: high.* Pure Python, no protocol changes, zero false positives by construction.
2. **Commit-reveal plan enforcement (`aigis.plan`).** *Effort: 1–2 weeks. Impact: very high.* Forces agents to declare tool sequences up front; mid-flight injection becomes structurally impossible.
3. **AIP-aligned capability tokens with slashable bond (`aigis.cap`).** *Effort: 4–8 weeks; needs ecosystem buy-in. Impact: paradigm-shifting if it lands.*
