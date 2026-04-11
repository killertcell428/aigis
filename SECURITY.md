# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.3.x   | :white_check_mark: |
| 1.2.x   | :white_check_mark: |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :x:                |
| 0.x.x   | :x:                |

Security patches are released only for the latest minor version.

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

1. **Acknowledgment** — We will confirm receipt within 72 hours.
2. **Assessment** — We will evaluate the impact and severity within 7 days.
3. **Fix** — We will develop and test a patch.
4. **Disclosure** — We will coordinate the release date with the reporter and publish a GitHub Security Advisory.
5. **Credit** — With the reporter's permission, we will credit them in the advisory and CHANGELOG.

We follow a [responsible disclosure](https://en.wikipedia.org/wiki/Responsible_disclosure) policy. We ask for a reasonable grace period (typically 90 days) before public disclosure.

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
