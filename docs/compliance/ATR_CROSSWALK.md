# Aigis <-> Agent Threat Rules (ATR) Crosswalk

> Last updated: 2026-07-02
> Reference: [MITRE ATLAS](https://atlas.mitre.org/) and [Agent Threat Rules (ATR)](https://github.com/Agent-Threat-Rule/agent-threat-rules) (MIT)
> Companion to [MITRE_ATLAS_COVERAGE.md](./MITRE_ATLAS_COVERAGE.md)

## Overview

Aigis and ATR are close cousins: both are deterministic, paper-grounded,
no-LLM detection layers for agent attacks. Aigis exposes stable pattern IDs;
ATR ships a ruleset where every rule carries a MITRE ATLAS reference block.
That shared MITRE ATLAS axis makes a clean crosswalk feasible.

This document maps Aigis detection patterns to ATR rules through the ATLAS
technique they both address, and lays out the ATLAS coverage gap in both
directions: techniques one project covers and the other does not.

The value is bidirectional. A team standardised on ATR rule IDs can find the
Aigis pattern that enforces the same technique at runtime; a team running Aigis
can find the ATR rules that extend coverage past what input/output pattern
matching reaches.

Requested in [killertcell428/aigis#153](https://github.com/killertcell428/aigis/issues/153).

## Method and evidence discipline

Every row below is verified, not inferred:

- Aigis pattern IDs are read from the DetectionPattern definitions in
  aigis/filters/patterns.py and aigis/patterns.py. IDs that do not exist in
  source are not listed.
- ATR rule IDs are read verbatim from each rule's id field and its
  references.mitre_atlas block in the Agent-Threat-Rule/agent-threat-rules
  repository (branch main). Each rule ID cited here was confirmed to return HTTP
  200 from the GitHub contents API on main before inclusion. None are authored
  by hand.
- A row is included only when the Aigis pattern exists, the ATR rule(s) exist,
  and both genuinely address the same ATLAS technique. Speculative rows are
  omitted.

The ATR rule IDs are exemplars, not the exhaustive set — ATR often carries dozens
of rules per technique. The last table column gives the full count observed in
ATR metadata so the exemplars are not mistaken for the whole.

### A note on ATLAS numbering

The crosswalk is anchored on the canonical MITRE ATLAS technique identified by
the current official ATLAS ID. ATR's references.mitre_atlas values already use
current official IDs (AML.T0057 = LLM Data Leakage, AML.T0056 = Extract LLM
System Prompt, AML.T0053 = AI Agent Tool Invocation, AML.T0110 = AI Agent Tool
Poisoning, and so on). Aigis's MITRE_ATLAS_COVERAGE.md was written against an
earlier ATLAS revision and, in places, uses older or non-standard technique
numbers (for example it labels AML.T0057 as "LLM Plugin Compromise" and
introduces AML.T0066 through AML.T0072 identifiers not in the current ATLAS
matrix). To avoid propagating that drift, each row is matched by the technique
itself, tagged with the current official ATLAS ID, and mapped to the Aigis
pattern by what that pattern actually detects — not by the label in the older
coverage doc. Reconciling MITRE_ATLAS_COVERAGE.md to current ATLAS IDs is tracked
as a follow-up in the gap analysis below.

---

## The crosswalk

Shared canonical ATLAS techniques where both projects have a real detection.

| ATLAS technique | Aigis pattern(s) | ATR rule(s) (exemplars) | ATR rules for this technique | Note |
|---|---|---|---|---|
| AML.T0051 — LLM Prompt Injection | pi_ignore_instructions, pi_new_instructions | ATR-2026-00001, ATR-2026-00004 | 396 | Instruction-override injection. Aigis screens the input string; ATR matches the same intent across the user-input and tool-channel fields. |
| AML.T0051.001 — LLM Prompt Injection: Indirect | ii_context_poisoning, ii_hidden_instruction, ii_tool_abuse | ATR-2026-00002, ATR-2026-00010, ATR-2026-00011 | 74 | Injection arriving via retrieved or tool content. Aigis exposes a scan_rag_context API plus the ii_* family; ATR covers the tool-output and RAG channels. |
| AML.T0054 — LLM Jailbreak | jb_developer_mode, jb_no_restrictions, pi_jailbreak_dan | ATR-2026-00003, ATR-2026-00143, ATR-2026-00144 | 139 | Guardrail or persona bypass. Broadest overlap after T0051. |
| AML.T0056 — Extract LLM System Prompt | pi_system_prompt_leak, pl_repeat_back_verbatim | ATR-2026-00020, ATR-2026-00061 | 8 | System or base-prompt extraction. Aigis's pl_* verbatim-echo family aligns tightly here. |
| AML.T0057 — LLM Data Leakage | out_secret_leak, out_pii_ssn, exfil_api_keys | ATR-2026-00021, ATR-2026-00113, ATR-2026-00114 | 90 | Secret or PII disclosure through model output. Aigis's output filter maps to ATR context-exfiltration rules. |
| AML.T0053 — AI Agent Tool Invocation | ii_tool_abuse | ATR-2026-00011, ATR-2026-00012, ATR-2026-00050 | 36 | Manipulated or unauthorised tool calls. |
| AML.T0110 — AI Agent Tool Poisoning | mcp_cross_tool_shadow | ATR-2026-00103, ATR-2026-00161, ATR-2026-01775 | 3 | Poisoned tool or MCP manifest carrying hidden instructions. Aigis's mcp_* family maps to ATR tool-poisoning rules. |
| AML.T0080 — AI Agent Context Poisoning | mem_cross_session_persistence, mem_experience_hijack | ATR-2026-00075, ATR-2026-00125, ATR-2026-00551 | 3 | Persistent memory or context contamination across turns or sessions. |
| AML.T0070 — RAG Poisoning | ii_context_poisoning | ATR-2026-00448, ATR-2026-00450 | 2 | Poisoned retrieval or memory-store content. |
| AML.T0024 — Exfiltration via AI Inference API | exfil_send_to_external, exfil_api_keys | ATR-2026-00063, ATR-2026-00217 | 27 | Data siphoned through the inference or tool path. |
| AML.T0025 — Exfiltration via Cyber Means | ii_exfil_via_markdown, exfil_send_to_external | ATR-2026-00405, ATR-2026-01753 | 6 | Out-of-band exfil such as a markdown image beacon or an external network post. |
| AML.T0050 — Command and Scripting Interpreter | cmdi_shell, cmdi_path_traversal | ATR-2026-00040, ATR-2026-00110 | 19 | Interpreter-invocation attempts on the input side. |
| AML.T0105 — Escape to Host | se_container_escape, afe_python_mro_escape | ATR-2026-00436, ATR-2026-00539 | 3 | Sandbox or container escape reaching the host. |
| AML.T0010 — AI Supply Chain Compromise | sc_compromised_pkg_version | ATR-2026-00060, ATR-2026-00062, ATR-2026-00065 | 38 | Compromised skill, package, or dependency in the agent supply chain. |
| AML.T0109 — AI Supply Chain Rug Pull | mcp_rug_pull_indicator | ATR-2026-00126 | 1 | Benign-then-malicious tool or skill update. Aigis flags version/update language paired with new sensitive-data access; ATR carries the rug-pull setup rule. |

**15 verified rows.** Coverage checked against 264 DetectionPattern definitions in
aigis/filters/patterns.py (the reproducible Aigis pattern inventory; 297 total id=
entries exist across the package once re-exports and scorer heuristics are
included). The 40 distinct ATR rule IDs referenced across this document and the gap
tables were each confirmed present on the Agent-Threat-Rule/agent-threat-rules main
branch.

---

## ATLAS coverage gap analysis

Both projects were reduced to the set of canonical ATLAS techniques they actually
detect (Aigis patterns to technique by detection behaviour; ATR rules to
technique by their references.mitre_atlas value, base technique only). The two
sets are compared below.

- Aigis: 15 canonical ATLAS techniques surfaced as crosswalk rows above, plus
  AML.T0088 (Generate Deepfakes), which synth_deepfake_request detects but which is
  not tagged to that ATLAS ID in source.
- ATR: 34 canonical ATLAS techniques referenced in rule metadata.
- Shared: the 15 techniques in the crosswalk above.

### (a) Techniques Aigis covers that ATR has no rule for

None. Every ATLAS technique an Aigis pattern detects is also carried by one or
more ATR rules. There is no runtime technique in Aigis's pattern set that ATR
leaves uncovered. This direction of the gap is empty — a useful result on its
own: for the input/output runtime layer, ATR is a strict superset of Aigis's
technique coverage.

### (b) Techniques ATR covers that Aigis has no pattern for

These are the 19 canonical ATLAS techniques present in ATR rule metadata with no
corresponding Aigis detection pattern. They split into two groups.

Group 1 — Runtime-detectable; candidate Aigis patterns. These occur in the
prompt, output, or tool stream Aigis already inspects, so a pattern is plausible:

| ATLAS technique | ATR rule(s) (exemplars) | Why it is a candidate for Aigis |
|---|---|---|
| AML.T0069 — Discover LLM System Information | ATR-2026-01303, ATR-2026-01772 | Recon prompts that enumerate tool schemas or internal state — a screenable input pattern. |
| AML.T0060 — Publish Hallucinated Entities | ATR-2026-00260 | Hallucinated package or dependency names in output, matchable against a package-name heuristic. Aigis has related synth_* and hal_* families but no pattern tied to this technique. |
| AML.T0102 — Generate Malicious Commands | ATR-2026-00413 | Output-side generation of harmful command or malware strings — a screenable output pattern Aigis does not yet carry. |
| AML.T0104 — Publish Poisoned AI Agent Tool | ATR-2026-00060 | A malicious tool or skill published for others to install — screenable in tool-manifest scanning (mcp_scanner). |
| AML.T0034 — Cost Harvesting | (ATR carries one rule for this technique) | Token or compute exhaustion for cost damage. Aigis has a token_exhaustion family under a DoS framing but not this technique specifically. |

One technique sits between the two directions and is not a gap: AML.T0088 —
Generate Deepfakes. Aigis has synth_deepfake_request, which detects requests to
synthesise deepfake or impersonating media, and ATR carries one rule for this
technique (ATR-2026-00706). It is not surfaced as a crosswalk row above because
the Aigis pattern is not tagged to this ATLAS ID in source; it is recorded here
so the technique is not misread as absent from Aigis.

Group 2 — Training-time, model-artifact, or infrastructure. These sit outside the
input/output runtime boundary Aigis inspects (they concern datasets, model files,
model access, or pre-interaction activity). They are correctly outside Aigis's
current scope and are listed for completeness, not as gaps to close:

AML.T0011 (Unsafe AI Artifacts / Malicious Package),
AML.T0018 (Poison AI Model),
AML.T0019 (Publish Poisoned Datasets),
AML.T0020 (Poison Training Data),
AML.T0036 (Data from Information Repositories),
AML.T0040 (AI Model Inference API Access),
AML.T0043 (Craft Adversarial Data),
AML.T0044 (Full AI Model Access),
AML.T0046 (Spamming AI System with Chaff Data),
AML.T0047 (AI-Enabled Product or Service),
AML.T0048 (External Harms),
AML.T0049 (Exploit Public-Facing Application),
AML.T0052 (Spearphishing),
AML.T0055 (Unsecured Credentials).

Two of these (AML.T0043, AML.T0048) appear as owasp_ref strings inside
aigis/filters/patterns.py, but under the earlier ATLAS numbering where those IDs
meant different techniques (AI Privilege Escalation, Sandbox Escape). They are
kept in this list rather than the crosswalk because, under the current official
ATLAS matrix, no Aigis pattern maps cleanly to the canonical technique those IDs
now denote. Correcting those in-code owasp_ref labels — and updating
MITRE_ATLAS_COVERAGE.md to current ATLAS IDs — is the concrete follow-up this gap
analysis surfaces.

---

## Regenerating this crosswalk

The Aigis inventory comes from the DetectionPattern definitions in
aigis/filters/patterns.py and aigis/patterns.py. The ATR side comes from each
rule's id field and its references.mitre_atlas value on the
Agent-Threat-Rule/agent-threat-rules main branch. Both are mechanically
extractable, so this document can be regenerated when either side changes; the
rule counts above are point-in-time as of the "Last updated" date and drift as
ATR ships rules.
