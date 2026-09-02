# 2. Control Matrix

This table maps each control Aigis implements to the major security and AI-governance frameworks. ISO/IEC 27001 item numbers are listed as "supports evidence for" — Aigis is a control implementation, not a certification body, and does not guarantee compliance.

**Two things to know before reading the table.** First, the IDs in the *AI Business Operator GL* column (`GL-*`, `SEC-*`, `APPI-*`) are **defined by Aigis**, derived from the guideline text — they are not official clause numbers, so asking which guideline clause `GL-POISON-01` refers to has no answer outside this repository. The requirement text behind each ID lives in `aigis/compliance.py`. Second, every mapping here is **self-assessed**: no third party has reviewed it, and the list contains no partial or uncovered entries — so read it as a statement of what we implement, not as a measured coverage figure.

| Aigis control | What it does | ISO/IEC 27001:2022 Annex A | NIST AI RMF | OWASP LLM Top 10 | AI Business Operator GL v1.2 |
|---|---|---|---|---|---|
| Input scanning (prompt-injection / jailbreak / PII) | Deterministic regex + similarity detection on every prompt before it reaches the model. | A.8.16 (Monitoring activities), A.5.7 (Threat intelligence) | MEASURE 2.7, MANAGE 2.1 | LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure | GL-POISON-01, SEC-PI-01 |
| Output scanning (data leak / secret / PII) | Scans model output for leaked secrets, PII, and system-prompt disclosure before it is returned. | A.8.12 (Data leakage prevention), A.5.34 (Privacy and PII) | MEASURE 2.7, MANAGE 4.1 | LLM02 Sensitive Information Disclosure, LLM05 Improper Output Handling | APPI-PII-01, GL-DATA-01 |
| Tool-call policy enforcement | Deterministic allow/deny/review decision on every tool call (shell, file, network) before execution. | A.8.18 (Use of privileged utility programs) | GOVERN 1.1, MANAGE 2.1 | LLM06 Excessive Agency | GL-HUMAN-03 (最小権限), SEC-PRIV-01 |
| MCP tool-definition scanning | Detects tool-poisoning and rug-pull changes in Model Context Protocol server definitions. | A.5.21 (ICT supply chain security), A.5.19 (Information security in supplier relationships) | MAP 4.1, MANAGE 3.1 | LLM03 Supply Chain, LLM01 Prompt Injection | GL-SEC-03 (攻撃対象面の管理) |
| Memory / file-write filter | Blocks writes to protected paths (.env, credentials, SSH keys) and filters persisted agent memory. | A.8.3 (Information access restriction), A.8.12 (Data leakage prevention) | MANAGE 2.1, GOVERN 1.4 | LLM06 Excessive Agency, LLM02 Sensitive Information Disclosure | GL-HUMAN-03 (最小権限), GL-DATA-02 |
| Tamper-evident audit log (HMAC + hash chain) | Append-only log; each entry HMAC-SHA256 signed and hash-chained so deletion/modification is detectable. | A.8.15 (Logging), A.8.16 (Monitoring activities), A.5.28 (Collection of evidence) | MEASURE 2.8, MANAGE 4.1 | LLM06 Excessive Agency (logging & monitoring) | GL-AUDIT-01 (追跡可能性), GL-RISK-02 (インシデントDB) |
| SIEM forwarding (ECS / HTTP) | Optional non-blocking forwarder mirrors events to a SIEM in Elastic Common Schema; PII redaction runs first. | A.8.16 (Monitoring activities), A.5.25 (Assessment of security events) | MEASURE 2.8, MANAGE 4.1 | LLM06 Excessive Agency | GL-HUMAN-04 (継続的モニタリング) |
| Weekly security report | Automated weekly report of scans, blocks, OWASP coverage, and week-over-week trend for review meetings. Cross-cutting — it aggregates the other controls rather than mapping to its own OWASP risk category. | A.5.36 (Compliance review), A.8.16 (Monitoring activities) | MEASURE 4.1, GOVERN 4.1 | — | GL-TRANS-01 (ドキュメント化), GL-RISK-02 |

## What Aigis does NOT cover

For an honest scope boundary, the following areas are **out of scope** for Aigis and must be handled by other controls (your existing security tooling and operational processes).

- Model training / fine-tuning safety — Aigis does not train or align models.
- Content moderation policy decisions — Aigis flags categories but does not define your acceptable-use policy.
- Network-layer DLP — egress filtering at the network boundary is your existing CASB/proxy's job.
- Endpoint security (EDR/antivirus) — Aigis governs the agent, not the host machine.
- Claude Code's own cloud-side processing — prompts sent to Anthropic are governed by Anthropic's terms, not by Aigis.
- Identity and access management — user authentication and SSO remain your IdP's responsibility.
