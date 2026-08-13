# Pending Design Decisions — Phase 3-4

> Status: **Decisions settled, code on master — but never released as "v1.5.0".**
> Updated: 2026-08-13 (status corrected)

## Version note (corrected 2026-08-13)

This file read "ALL PHASES COMPLETE — v1.5.0 RELEASED" from 2026-04-11 until
2026-08-13. **No such release exists.** The tag list tops out at **v1.2.0**
(2026-08-09); v1.3.0, v1.3.1, v1.4.0 and v1.5.0 were never tagged either, even
though the April ROADMAP credited shipped features to them.

What actually happened: the decisions below were settled and the code landed on
master, but version numbers in the planning docs ran ahead of the tags. The
`v1.1.12` note in [CHANGELOG.md](CHANGELOG.md) records a related failure — a tag
cut from a branch HEAD that never reached master, caught by the orphan-tag guard
in `release.yml`.

So: treat the **decisions** below as authoritative and the **version numbers** as
not. [pyproject.toml](pyproject.toml) is the only source of truth for the current
version (1.2.0). The root `package.json` still says 1.3.1; it is unrelated to the
published package and is not the version anyone should read.

## Phase 1-2 (v1.4.0): COMPLETED AND RELEASED

All decisions resolved, released as v1.4.0.

---

## Phase 3-4 Decisions (to confirm after implementation)

### Decision 7: Policy DSL Syntax

AgentSpec-style runtime constraint DSL. What syntax?

| Option | Pros | Cons |
|--------|------|------|
| A) YAML-based rules with predicates (Recommended) | Consistent with existing policy.yaml, zero learning curve | Less expressive than custom DSL |
| B) Custom DSL (Python-like syntax) | Most expressive, AgentSpec paper uses this | Parser complexity, new syntax to learn |

**Current plan:** A (YAML-based, extends existing format with triggers/predicates/enforcement actions)

### Decision 8: Cryptographic Signing for Audit Logs

| Option | Pros | Cons |
|--------|------|------|
| A) HMAC-SHA256 with hash chain (Recommended) | stdlib only (hmac module), simple key management | Shared secret — key compromise = forge all logs |
| B) Ed25519 asymmetric signatures | Strongest guarantees, no shared secret | Requires `cryptography` package (optional dep) |

**Current plan:** A (HMAC-SHA256, stdlib only). Ed25519 as optional upgrade path.

### Decision 9: Cross-Session Storage Backend

| Option | Pros | Cons |
|--------|------|------|
| A) JSON files (Recommended) | Zero dependencies, consistent with project philosophy | Slower queries on large datasets |
| B) SQLite | Built into Python stdlib, better querying | File locking issues on some platforms |

**Current plan:** A (JSON files). SQLite as optional optimization.

### Decision 10: Supply Chain Hash Pinning — Default Mode

| Option | Pros | Cons |
|--------|------|------|
| A) Opt-in (warn only by default) (Recommended) | Low adoption friction | Tools can change without notice if user doesn't enable |
| B) Mandatory (block unverified tools) | Maximum security | Breaks if tool definitions update legitimately |

**Current plan:** A (opt-in with warnings)

---

## Implementation Status — Phase 3-4

| Module | Status | Agent |
|--------|--------|-------|
| `spec_lang/parser.py` | ✅ Done (YAML + fallback, Trigger/Predicate/Enforcement) | Phase 3a agent |
| `spec_lang/evaluator.py` | ✅ Done (RuleEvaluator, custom predicates) | Phase 3a agent |
| `spec_lang/stdlib.py` + `defaults.py` | ✅ Done (9 built-in predicates, 7 default rules) | Phase 3a agent |
| `audit/signed_log.py` | ✅ Done (HMAC-SHA256, auto key gen) | Phase 3b agent |
| `audit/chain.py` | ✅ Done (SHA-256 hash chain) | Phase 3b agent |
| `audit/verify.py` | ✅ Done (4 checks: sig/chain/seq/time) | Phase 3b agent |
| `supply_chain/hash_pin.py` | ✅ Done (SHA-256 pinning, thread-safe) | Phase 4a agent |
| `supply_chain/sbom.py` | ✅ Done (CycloneDX 1.5, 20 package prefixes) | Phase 4a agent |
| `supply_chain/verify.py` | ✅ Done (known vuln DB: litellm, ultralytics) | Phase 4a agent |
| `cross_session/store.py` | ✅ Done (JSON file-based, path traversal safe) | Phase 4b agent |
| `cross_session/correlator.py` | ✅ Done (4 correlation checks, z-score outlier) | Phase 4b agent |
| `cross_session/sleeper.py` | ✅ Done (3 detection methods, E2E test) | Phase 4b agent |
| Integration + Tests | ✅ 901 tests pass | — |
| **Security Review** | ✅ 23 findings, 6 fixed (Critical/High) | Explore agent |
| Fix review findings | ✅ Applied to audit/store/verify/stdlib/hash_pin | — |
| CHANGELOG + Release | ✅ v1.5.0 released | — |
| CodeQL alerts | ✅ 17/17 resolved | — |
| Dependabot alerts | ✅ 14/14 resolved (Next.js 16.2.3) | — |
