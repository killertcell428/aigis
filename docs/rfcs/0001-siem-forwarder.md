# RFC 0001 — SIEM / log forwarder layer

> Status: **Draft** · Author: @s1ns3nz0 · Phase 1 reference implementation
> shipped on `feat/siem-forwarder` (this PR).

## Summary

Add a Tier-4 outbound sink — `aigis/forwarders/` — that mirrors every
`ActivityEvent` to external SIEM / log-lake systems (Splunk HEC, Elastic,
Microsoft Sentinel, Datadog, in-house ingest endpoints) without blocking
the agent hot path and without changing the on-disk JSONL tiers.

This lands the Phase 3 roadmap item
[`ROADMAP.md`](../../ROADMAP.md) line 160 ("SIEM integration") as a vertical
slice: foundation + ECS schema mapper + one universal transport (HTTPS
JSON), all in stdlib-only Python so the zero-dep core is preserved.

## Motivation

`ActivityStream` (`aigis/activity.py`) already captures the right events
with the right fields (`user_id`, `risk_score`, `policy_decision`,
`matched_rules`, `owasp_refs`, `autonomy_level`, `delegation_chain`).
`SignedAuditLog` (`aigis/audit/`) gives those events a tamper-evident chain.

But until the events reach the enterprise SOC, several controls stay
checked-in-letter-but-not-in-spirit:

* **ISMS-P 2.9 / 2.11** require log management and 이상행위 분석 *in the
  organisation's central monitoring stack* — local JSONL is not enough.
* **금융위 AI 가이드라인 (2024)** treats LLM-side anomalies as a category
  of 이상행위 탐지; they have to land in the same SOC pipe as everything
  else.
* **Insider-threat / UEBA** correlation needs Aigis signals next to IdP,
  EDR, and DLP signals — that means the SIEM, not a developer's `~/.aigis/`.
* **NIST SP 800-53 AU-2 / AU-6** ("audit events" / "audit review") implies
  centralized review, not per-host log files.

## Goals

1. Add a clean extension point so anyone can plug in a forwarder for their
   SIEM with ~50 LOC of subclass code.
2. Ship a default ECS schema mapper that works for Elastic, Sentinel
   (via DCR), Wazuh, and is straightforward to re-map to Splunk CIM.
3. Preserve every Aigis-native field — `matched_rules`, `owasp_refs`,
   `autonomy_level`, `delegation_chain`, `policy_decision` — verbatim so
   analysts never lose information.
4. Make it physically impossible for a misconfigured or down SIEM to
   slow down, error out, or block an agent tool call.
5. Zero new required dependencies. Transports that need third-party clients
   (e.g. azure-identity for Sentinel managed-identity) go into extras.

## Non-goals (this RFC)

* Pre-built Splunk ES correlation rules or Sentinel analytic rules —
  separate RFC, separate repo cadence.
* Pre-built Sigma detection rule bundle — Phase 4 in the original plan.
* Authentication-flow wrappers per vendor (OAuth refresh, IAM signing) —
  ship as optional subclasses once Phase 1 is merged.

## Design

### Pipeline

```
ActivityStream.record(event)
  ├─ Tier 1: local  JSONL  (unchanged, always)
  ├─ Tier 2: global JSONL  (unchanged, if enabled)
  ├─ Tier 3: alerts JSONL  (unchanged, if is_alert)
  └─ Tier 4: for fwd in self._forwarders: fwd.submit(event)
              └─ enqueue onto bounded background queue → worker thread
                  └─ redact (in-memory dict, before mapping)
                  └─ map   (ActivityEvent → ECS dict, default)
                  └─ batch (size + interval thresholds)
                  └─ ship  (HTTPS POST, with retry policy)
```

The dispatch order matters: the local JSONL tiers are written
*synchronously* and *first*, so they remain authoritative even if the
forwarder layer is misbehaving.

### Class shape

```python
class LogForwarder(ABC):
    def submit(self, event: ActivityEvent) -> None: ...     # never blocks, never raises
    def close(self, timeout: float = 5.0) -> None: ...
    @property
    def stats(self) -> dict[str, int]: ...                  # sent / dropped / queued

    @abstractmethod
    def _ship(self, batch: list[dict]) -> None: ...         # subclass hook

class EventMapper(Protocol):
    def map(self, event: dict) -> dict: ...

class Redactor(Protocol):
    def redact(self, event: dict) -> dict: ...
```

* `Redactor` runs *before* the mapper, on the raw Aigis dict, so PIPA /
  GDPR rules are written against the native field names.
* `EventMapper` is a Protocol (not ABC) so adding CEF / OCSF / Splunk CIM
  is a single file with no inheritance dance.

### Schema — why ECS as default

| Vendor / consumer | ECS support |
|---|---|
| Elastic / Wazuh | Native index pattern, no transform |
| Microsoft Sentinel | Log Ingestion API + DCR consumes ECS JSON directly |
| Splunk | One CIM transform per field (mappable from ECS) |
| OSS SIEMs (SecurityOnion, OpenSearch SIEM) | Native |

ECS is the only schema where the same `event.action` / `user.name` /
`process.command_line` mapping works across the three biggest enterprise
SIEMs. OCSF is gaining momentum (AWS Security Lake) but is not yet
broadly consumed — recommended as a follow-up mapper, not the default.

### Failure isolation

| Failure mode | Behavior |
|---|---|
| SIEM unreachable | Worker retries 5xx with exponential backoff; on exhaustion the batch is dropped (still in local JSONL); counter incremented. |
| SIEM returns 4xx | No retry (misconfig). Logged once per batch; counter incremented. |
| Forwarder thread crashes | Caught at `record()` boundary; agent continues; logged. |
| Queue full | Drop oldest pending event, enqueue newest; counter incremented. |
| Mapper raises | Single event dropped; counter incremented; worker continues. |
| Redactor raises | Single event dropped *before mapping*; counter incremented. |

The invariant: **no forwarder failure mode can stop the agent or corrupt
the on-disk JSONL.**

### Compatibility

* New code is fully opt-in. `ActivityStream._forwarders` defaults to `[]`
  and `record()` skips Tier 4 entirely when the list is empty — the hot
  path is unchanged for users who don't register a forwarder.
* No new required dependencies. `pyproject.toml` is not modified by this
  PR; vendor-specific subclasses will introduce extras in follow-up PRs.
* No public API removed or renamed.

## Reference implementation

Phase 1 ships in this PR:

```
aigis/forwarders/
├── __init__.py              # re-exports stable public symbols
├── base.py                  # LogForwarder ABC, Redactor protocol, worker
├── http_json.py             # generic HTTPS JSON sink (stdlib only)
└── schema/
    ├── __init__.py
    └── ecs.py               # ActivityEvent → ECS 8.11.0

aigis/activity.py            # +50 LOC: add_forwarder / remove_forwarder /
                             #          close_forwarders + record() dispatch

docs/forwarders.md           # quickstart (Splunk HEC / Sentinel / Elastic)
docs/rfcs/0001-siem-forwarder.md  # this document

tests/test_forwarders.py     # 14 new tests
```

**Tests: 1726 pass · 0 fail · 14 new in `test_forwarders.py`.**

## Scope

This PR is the **foundation slice only**. Per the discussion on
[killertcell428/aigis#98](https://github.com/killertcell428/aigis/issues/98),
the following items are explicitly *out of scope* and will each get their
own follow-up issue once this lands:

- Vendor-specific transports — `SyslogForwarder` (RFC 5424),
  `SplunkHECForwarder`, `SentinelForwarder` (DCR-aware).
- An OCSF mapper as a sibling of `ECSMapper`.
- Durable on-disk queue spool (see Resolved decision #3 below).
- Detection-content bundles — Sigma rules, Splunk ES / Sentinel analytic
  rule sidecars.
- KR-specific compliance presets (`compliance_kr.py` ISMS-P 2.9 / 2.11
  status refresh, PIPA `Redactor` preset) — separate PR on the KR fork
  after upstream lands.

## Resolved design decisions

Following the discussion on
[killertcell428/aigis#98](https://github.com/killertcell428/aigis/issues/98):

1. **Default schema → ECS 8.x.** Decision: ship ECS as the default mapper.
   Keep the `EventMapper` Protocol seam so OCSF can be added as a sibling
   mapper in a follow-up, *but do not ship the OCSF mapper in this PR*.
   Rationale: ECS has the broadest installed consumer base across Splunk
   (via CIM), Sentinel (via DCR), Elastic, and Wazuh — matching what JP/KR
   enterprise SOCs are actually running today.

2. **Module location → new `aigis/forwarders/` package.** Decision:
   `aigis/middleware/` is reserved for LLM-provider request/response
   proxies (Anthropic, OpenAI, LangChain, LangGraph, FastAPI), which is
   semantically different from outbound log shipping. The maintainer will
   update `CONTRIBUTING.md` to add a "log forwarders" section pointing at
   the new package as part of the merge.

3. **Queue persistence → defer to a follow-up issue.** Decision: ship the
   foundation with the in-memory bounded queue only. Persisting the tail
   across crashes (SQLite WAL spool, ~150 LOC) introduces an integrity
   contract with the JSONL tier that warrants its own design, ideally
   driven by an actual incident report ("we lost N events when the SIEM
   was down for M hours").

   > **TODO (follow-up issue):** durable on-disk spool for the forwarder
   > queue. Open after the foundation lands and the first real outage
   > tells us the loss model we are pricing.

4. **PII redaction defaults → preserve fields; document Redactor as a
   required configuration step.** Decision: keep the current
   preserve-by-default behavior. Stripping `details` / rule sample text
   silently would erase analyst signal, which is worse than a
   documented-but-explicit configuration step. Future work: ship a
   "KR PIPA preset" and a "JP APPI preset" `Redactor` in a follow-up.

   For compliance contexts (PIPA, GDPR, APPI, ISMS-P) the `Redactor`
   is **a required configuration step**, not optional. Operators of
   those deployments must wire one before enabling the forwarder. The
   minimum viable shape is:

   ```python
   class _PipaPreset:
       def redact(self, event: dict) -> dict:
           event.pop("details", None)
           event.pop("matched_rules", None)  # may contain rule sample text
           return event

   stream.add_forwarder(
       HTTPJsonForwarder(url=..., redactors=[_PipaPreset()])
   )
   ```

   See `docs/forwarders.md` for the SOC-engineer-facing version.

## Acceptance criteria

* `uv run pytest` is green (currently 1726 pass).
* `uv run ruff check aigis/forwarders/ tests/test_forwarders.py aigis/activity.py`
  is clean.
* New code adds no required dependencies (`pyproject.toml` unchanged).
* `ActivityStream` with no forwarders registered behaves identically to
  master (covered by the existing `tests/test_activity.py` suite, all 19
  pre-existing tests still pass).
