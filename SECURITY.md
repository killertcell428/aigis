# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| 0.x.x   | :x:                |

Security patches are released only for the latest minor version. Pre-1.0
releases are no longer supported as of v1.0.0 (2026-05-07).

## Reporting a Vulnerability

**Please do not create a public GitHub Issue for security vulnerabilities.**

### Method 1 — GitHub Private Security Advisory (Recommended)

1. Navigate to the repository's **Security** tab → **Advisories** → **New draft security advisory**.
2. Fill in the details (description, affected versions, reproduction steps, proposed fix).
3. Submit. A maintainer will respond within **72 hours**.

### Method 2 — Email

Send the following information to **security@killertcell428.dev**:

- Description of the vulnerability
- Reproduction steps
- Affected versions
- Known mitigations
- Contact information (optional, for acknowledgment purposes)

PGP key: Available upon request.

## Response Process

We follow a [coordinated vulnerability disclosure](https://en.wikipedia.org/wiki/Responsible_disclosure) policy with the following service-level targets:

| Stage | Target | Notes |
| --- | --- | --- |
| **Acknowledgment** | ≤ 72 hours | Confirmation of receipt to the reporter |
| **Initial assessment** | ≤ 7 days | Impact, severity (CVSS v3.1), affected versions |
| **Fix availability** | ≤ 60 days (high/critical) <br> ≤ 90 days (medium/low) | Patched release published to PyPI + GHCR |
| **Public disclosure** | ≤ 90 days after report | GitHub Security Advisory + CVE if applicable |
| **Credit** | At advisory publication | With reporter's permission, in advisory + CHANGELOG |

If a fix cannot land within the target window, we will inform the
reporter and agree on an extension before disclosure. If an active
exploit is observed in the wild, we may shorten the timeline and
publish an advisory immediately alongside the patched release.

## Scope

The following is **in scope**:

- Bypass of `Guard` class detection logic (attacks exploiting false negatives)
- Information leakage from the library itself
- Remote code execution via crafted input
- Dependency vulnerabilities in published packages
- Security issues in the self-hosted backend (`backend/`)

The following is **out of scope**:

- Attacks requiring physical access to the host machine
- Social engineering against maintainers
- Third-party dependency issues that do not directly impact aigis

## Note on Security Design

aigis is **one layer of defense in depth** and is not a complete security solution. It operates by pattern matching against known attack patterns and should be used in combination with:

- Input validation at API boundaries
- Output sanitization before displaying to users
- Principle of least privilege for LLM system prompts
- Rate limiting and audit logging

Sophisticated attackers may craft inputs that evade the current pattern set. We continuously maintain and expand detection patterns, and welcome contributions through the standard PR process.
