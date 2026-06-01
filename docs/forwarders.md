# SIEM forwarders

> Mirror every Aigis event into Splunk, Elastic, Microsoft Sentinel, Datadog,
> or any in-house ingest endpoint — without blocking agent execution and
> without giving up the on-disk audit trail.

## Why

`ActivityStream` already writes three on-disk JSONL tiers (local / global /
alerts) and `aigis.audit.SignedAuditLog` keeps an HMAC-chained tamper-evident
log. Both are authoritative — but they live on the developer machine. For
audit response, insider-threat analytics, or 24/7 보안관제, the events have
to flow into the enterprise SOC's SIEM as well.

Forwarders are a Tier-4 sink that sits *next to* the local tiers, not in
place of them. If the SIEM goes down, the agent keeps running and the local
JSONL is still complete.

## Quick start — Splunk HEC

```python
from aigis.activity import ActivityStream
from aigis.forwarders import HTTPJsonForwarder, ECSMapper

stream = ActivityStream()
stream.add_forwarder(
    HTTPJsonForwarder(
        url="https://splunk.internal:8088/services/collector",
        headers={"Authorization": "Splunk <hec-token>"},
        body_format="ndjson",
        gzip_payload=True,
        mapper=ECSMapper(dataset="aigis.activity"),
    )
)
```

That is the whole integration. Every subsequent `stream.record(event)` call
(direct or via the Claude Code / Cursor adapters) is mirrored to Splunk on a
background thread.

## Quick start — Microsoft Sentinel

Sentinel's Log Ingestion API accepts ECS JSON via a Data Collection Rule.
Point the forwarder at the DCR endpoint and set the Bearer token from your
managed identity:

```python
HTTPJsonForwarder(
    url="https://<dce>.<region>-1.ingest.monitor.azure.com"
        "/dataCollectionRules/<dcr-immutable-id>/streams/Custom-Aigis_CL?api-version=2023-01-01",
    headers={"Authorization": f"Bearer {token}"},
    body_format="array",
    mapper=ECSMapper(dataset="aigis.activity", namespace="prod"),
)
```

## Quick start — Elastic

Elastic Common Schema is the default output, so a generic ingest pipeline
works without transforms:

```python
HTTPJsonForwarder(
    url="https://elastic.internal:9200/_bulk",
    headers={"Authorization": "ApiKey <key>"},
    body_format="ndjson",
    mapper=ECSMapper(dataset="aigis.activity", namespace="prod"),
)
```

## Redaction — required configuration step for compliance contexts

**If your deployment is subject to PIPA, GDPR, APPI, or ISMS-P, a
`Redactor` is a required configuration step, not optional.** The default
mapper preserves analyst-facing fields verbatim — `aigis.matched_rules`,
`aigis.details`, and the original `target` (which may be a shell command
containing user input or PII). Forwarding those fields to a SIEM operated
by a different data controller, or any SIEM at all in a regulated
deployment, without redaction is the operator's PIPA / GDPR /
APPI / ISMS-P incident.

Minimum viable redactor:

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

A richer example for defense-in-depth (mask home-directory paths in
`target`, strip oversized fields):

```python
class StripDetails:
    def redact(self, event: dict) -> dict:
        event.pop("details", None)
        if event.get("target", "").startswith("/home/"):
            event["target"] = "<home-dir>"
        return event

HTTPJsonForwarder(
    url=...,
    redactors=[StripDetails()],
)
```

Redactors run before the schema mapper, on the raw Aigis event dict — so you
write rules against `aigis.activity.ActivityEvent` field names, not ECS
paths. Pre-built jurisdiction-aware presets (KR PIPA, JP APPI) are a planned
follow-up; until then, write the preset that matches your own data
processing agreement.

## Schema

Default schema is **ECS 8.11.0**. The mapping preserves Aigis-native fields
under `aigis.*` so analysts never lose information when correlating against
upstream identity / network telemetry.

| Aigis field | ECS field | Notes |
|---|---|---|
| `timestamp` | `@timestamp` | ISO-8601 UTC |
| `action` (`shell:exec`, `file:read`, …) | `event.action`, `event.category` | Category derived from prefix |
| `policy_decision` (`allow` / `deny` / `review`) | `event.outcome` (`success` / `failure` / `unknown`) | Original verb kept at `aigis.policy.decision` |
| `risk_score` (0-100) | `event.risk_score` | Also exposed at `aigis.risk.score` |
| `risk_level` (`low` / `medium` / `high` / `critical`) | `event.severity` (2 / 4 / 6 / 7) | |
| `user_id` | `user.name` | |
| `cwd` | `process.working_directory` | |
| `target` | `process.command_line` | Single field; works for shell, file, URL targets |
| `matched_rules[0]` | `rule.name` | Full list at `aigis.matched_rules` |
| `policy_rule_id` | `rule.id` | |
| Blocked / reviewed / risk ≥ 50 | `event.kind = "alert"` | Otherwise `event.kind = "event"` |

Aigis-only fields (no ECS equivalent) live under `aigis.*`:
`autonomy_level`, `delegation_chain`, `memory_scope`, `estimated_cost_usd`,
`owasp_refs`, `remediation_hints`, `suggested_fix`, `fix_applied`, `details`.

## Operational notes

* **Non-blocking.** `HTTPJsonForwarder.submit()` enqueues onto a bounded
  `queue.Queue` and returns immediately. Default queue size is 10,000 events
  per forwarder; under saturation the oldest pending event is dropped (the
  on-disk JSONL still has it).
* **Counters.** `forwarder.stats` returns `{"sent": …, "dropped": …,
  "queued": …}` — wire these into `/aig doctor` for visibility.
* **Retry policy.** 5xx and network errors retry with exponential backoff
  (default 2 retries). 4xx errors do not retry — they indicate
  misconfiguration and noisy retries against a misconfigured endpoint
  amplify the problem.
* **TLS.** HTTPS is strongly recommended. HTTP works for in-VPC endpoints
  but emits a one-time warning to the `aigis.forwarders.http` logger.
* **Shutdown.** Call `stream.close_forwarders()` (or
  `forwarder.close()`) on process exit to drain the queue. The worker is a
  daemon thread, so abrupt exit will drop in-flight batches — these remain
  in the on-disk JSONL.

## Compliance mapping (한국 환경)

The on-disk JSONL alone satisfies the *existence* of `audit log` controls.
Forwarders close the *integration* gap that 감사관 / KISA / 금감원 검사관
typically point at:

| 통제항목 | 통합관제 갭이 메우는 부분 |
|---|---|
| ISMS-P 2.9 (로그관리) | "타 시스템 로그와 통합·상관분석" — 단일 SIEM 으로 흘려보내면 충족 |
| ISMS-P 2.11 (이상행위 분석) | UEBA / 상관규칙은 SIEM 측에서 구동 — Aigis 는 신호원 |
| 금융위 AI 가이드라인 (2024) "이상행위 탐지" | Aigis `risk_score ≥ 50` 이벤트가 `event.kind = "alert"` 로 SIEM 알람 파이프라인에 합류 |
| PIPA 영 §30 (안전성 확보조치) 접속기록 보관 | `aigis.audit.SignedAuditLog` 무결성 chain + SIEM 사본의 이중화 |

## Future transports

The base class is intentionally minimal. Planned follow-ups (each ~50 LOC
on top of `LogForwarder`):

* `SyslogForwarder` — RFC 5424 over UDP / TCP / TLS (stdlib only).
* `SplunkHECForwarder` — HEC-specific quirks (index, source, sourcetype,
  channel ID for ack mode).
* `SentinelForwarder` — DCR-aware client with managed-identity token
  refresh (optional `azure-identity` extra).
* `KafkaForwarder` — for environments that prefer log-bus → SIEM connector
  decoupling (optional `confluent-kafka` extra).
