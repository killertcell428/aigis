---
platform: reddit
subreddit: netsec
status: draft
---

# Reddit r/netsec draft — v0.0.4

## Title options

1. Audited my own OSS AI firewall and found 13 issues. Full disclosure + fixes in v0.0.4.
2. Aigis v0.0.4 — self-audit findings + 7 recent LLM-security papers implemented (zero deps)
3. Self-audit of an AI-firewall OSS: HMAC-less API keys, SSRF via Slack webhook, ReDoS-silent custom rules

(Recommend #1 — catchiest + honest.)

---

## Body

I maintain [Aigis](https://github.com/killertcell428/aigis), an OSS firewall for AI agents — 165+ detection patterns, MCP scanning, zero core dependencies. Shipping v0.0.4 today. Two parallel tracks landed:

### (1) Self-audit of the backend + scanner core

Critical 4 / High 5 / Medium 4 + 7 CodeQL alerts. Publishing the findings alongside the fixes because a security OSS that hides audits is strictly worse than one that publishes them. Highlights:

- **Unsalted SHA-256 + `==` for API keys.** DB-leak rainbow-table recovery + timing attack on verify. Replaced with HMAC keyed on the app secret + `hmac.compare_digest`.
- **Stripe webhook with no idempotency.** Retries doubled plan transitions. Added a `WebhookEvent(event_id UNIQUE)` ledger; dedup runs right after signature verification.
- **Slack webhook SSRF.** `tenant.slack_webhook_url` was admin-controlled and posted without validation — straight line to AWS IMDS. Fixed with `hooks.slack.com` allowlist + private/loopback/link-local rejection.
- **`custom_rules` regex: no ReDoS guard, errors swallowed silently.** A tenant could upload `(a+)+b` to freeze the scanner, or upload malformed patterns in bulk to silently disable detection. New `_regex_guard.safe_compile_user_regex()` rejects oversized patterns, nested quantifiers, and quantified alternation groups; broken rules now surface as an `invalid_rule` match instead of `except re.error: continue`.
- **`/admin/tenants POST` was unauthenticated** — literally commented as "no auth required for MVP". Now gated on `superadmin` role.
- **JWT: algorithms not pinned, `exp`/`sub`/`tenant_id` not required.** Tightened to `algorithms=["HS256"]` + `require` enforcement.
- **Production validators** added for `SECRET_KEY` placeholder and `postgres:postgres` DB credentials.

Plus confusables coverage expansion (Armenian, Hebrew, Arabic-Indic digits, Fullwidth Latin, zero-width and bidi control codepoints), bcrypt rounds=14 pinning, and the CodeQL cleanup on `py/overly-permissive-regex-range` (6×) and `py/clear-text-logging-sensitive-data` (1×).

All 13 findings + 7 CodeQL in the [CHANGELOG](https://github.com/killertcell428/aigis/releases/tag/v0.0.4).

### (2) Seven 2025–2026 LLM-security papers implemented, zero deps

Each module cites its paper in the docstring. Each one was mapped into an existing defence layer rather than bolted onto the side:

- **`filters.fast_screen`** — char-trigram LLR screen (Mirror Design Pattern, [arxiv:2603.11875](https://arxiv.org/abs/2603.11875)).
- **`filters.structured_query`** — StruQ/LLMail-Inject-style slot separation; raises `BoundaryViolation` on role-token leakage into the data slot.
- **`filters.rag_context_filter`** — DataFilter/RAGDefender-style per-chunk strip/block.
- **`spec_lang.fsm`** — MI9 goal-conditioned FSM; hard violations vs. statistical drift.
- **`memory.imitation_detector`** — MemoryGraft defence via Jaccard similarity on agent-voice references.
- **`mcp_scanner.scan_invocation` / `scan_response`** — MSB 3-stage coverage; extends MCP scanning from definitions to runtime args/responses.
- **`filters.patterns` — `judge_manipulation` category (15 patterns)** — AdvJudge-Zero-style forced-verdict / rubric-override phrasing.

Testing: 940/940 aigis core + 61/61 backend tests pass after the dual track.

### Why post here

Two things I'd welcome feedback on:

1. **Audit methodology.** I used a mix of CodeQL + manual review with LLM assistance. If your team has a better disclosure format for self-audits of security OSS (I'd like to publish a postmortem template), happy to compare notes.
2. **Paper-to-module pipeline.** I'd like to hear from anyone who's done research-to-production with defensive security papers. My heuristic so far: one module per paper, must map onto an existing architecture layer, zero new dependencies. Counterexamples welcome.

GitHub: https://github.com/killertcell428/aigis
