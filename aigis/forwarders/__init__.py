"""SIEM / log forwarders for Aigis.

Forwarders are optional sinks that mirror :class:`aigis.activity.ActivityEvent`
records into external systems (SIEMs, log lakes, message buses) for audit,
insider-threat analytics, and SOC integration. They run alongside the existing
local / global / alert JSONL tiers documented in :mod:`aigis.activity` — never
in place of them — so the on-disk audit trail and the
:class:`aigis.audit.SignedAuditLog` tamper-evident chain remain authoritative.

Design goals:

* **Hot-path non-blocking** — ``ActivityStream.record()`` enqueues onto a
  bounded background queue. Forwarder I/O never blocks an agent tool call.
* **Zero new required deps** — the base ABC, the ECS schema mapper, and the
  generic HTTP sink use only the Python standard library, preserving Aigis'
  zero-dependency core (see ``pyproject.toml``).
* **PII safety by default** — a :class:`Redactor` hook runs *before* the event
  ever leaves the process, so PIPA / ISMS-P deployments can strip rule sample
  text and other sensitive fields before they reach a SIEM operated by a
  different data controller.
* **Schema-stable wire format** — the default schema is Elastic Common Schema
  (ECS) 8.x, which is consumed natively by Elastic, ingested by Microsoft
  Sentinel via the Log Ingestion API, and re-mappable to Splunk CIM. CEF /
  OCSF mappers can be added without changing the dispatch path.

Quick start::

    from aigis.activity import ActivityStream
    from aigis.forwarders import HTTPJsonForwarder
    from aigis.forwarders.schema import ECSMapper

    stream = ActivityStream()
    stream.add_forwarder(
        HTTPJsonForwarder(
            url="https://siem.internal/api/aigis",
            headers={"Authorization": "Bearer <token>"},
            mapper=ECSMapper(dataset="aigis.activity"),
        )
    )

All public symbols re-exported here are stable; the submodules
(:mod:`aigis.forwarders.base`, :mod:`aigis.forwarders.http_json`,
:mod:`aigis.forwarders.schema`) are also importable directly.
"""

from aigis.forwarders.base import (
    ForwarderError,
    LogForwarder,
    Redactor,
)
from aigis.forwarders.http_json import HTTPJsonForwarder
from aigis.forwarders.schema import ECSMapper, EventMapper

__all__ = [
    "ECSMapper",
    "EventMapper",
    "ForwarderError",
    "HTTPJsonForwarder",
    "LogForwarder",
    "Redactor",
]
