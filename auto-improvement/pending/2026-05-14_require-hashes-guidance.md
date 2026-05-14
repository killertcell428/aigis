# Pending: `--require-hashes` and Sigstore Attestation Guidance Document

**Cycle:** 5 (third pass) · **Domain:** supply-chain-llm · **UTC:** 2026-05-14T06-06

## Title

Hash-pinning and Sigstore attestation verification guide for AI Python projects

## Motivation

The TanStack branch of the Mini Shai-Hulud campaign (May 2026) compromised packages using OIDC
token extraction from GitHub Actions runner memory (`/proc/*/mem`), impersonating the legitimate
release pipeline's Trusted Publisher OIDC identity. The resulting packages were published by
TanStack's own verified identity and passed PyPI Trusted Publisher checks — meaning version pinning
alone would not have prevented installation of the malicious packages if a user had pinned to the
compromised version.

The correct defense is a two-layered approach:
1. **Hash pinning** (`pip install --require-hashes -r requirements.txt`) — ensures every wheel and
   source distribution downloaded exactly matches a known cryptographic hash, regardless of who
   published it or via what CI identity.
2. **Sigstore/PEP 740 attestation verification** — starting in 2025, PyPI supports supply chain
   provenance attestations (Sigstore) for packages published via Trusted Publishers; tools like
   `pip`, `pypi-attestations`, and `uv` can verify these before installation.

## Which research finding led to this

The TanStack / Mini Shai-Hulud OIDC impersonation technique (May 2026, safedep.io, snyk.io,
hackread.com findings in research file `2026-05-14T06-06_5-supply-chain-llm.md`).

## Proposed change

Add `docs/hash-pinning-guide.md`:
- Explain why version pinning alone is insufficient against OIDC-impersonation supply chain attacks
- Show how to generate a `requirements.txt` with hashes using `pip-compile --generate-hashes` or
  `uv lock`
- Explain how to install with `pip install --require-hashes -r requirements.txt`
- Cover Sigstore attestation verification (`pip download --verify-attestations` or
  `pypi-attestations verify`)
- Include an aigis-specific example showing how to protect aigis itself (its own installation)

## Why it was held back

- Documentation-only change; does not add a detection rule
- The loop prefers combining documentation with at least one implementable rule; this cycle already
  had two implementable items and the documentation was lower priority
- The guide requires research into exact `uv` and `pip` CLI syntax to ensure accuracy

## Which constraint blocked it

No hard constraint — simply deprioritized in favor of the two implementable detection items.

## Suggested next step for the human reviewer

Pick this up in a `supply-chain-llm` or `compliance-regulation` cycle. The guide is short (< 2
pages) and directly actionable for any Python AI project. Verify current `uv` and `pip` attestation
CLI syntax before writing, as the PEP 740 tooling was still evolving as of May 2026.
