"""Wire-format mappers for forwarders.

A mapper transforms a serialized :class:`aigis.activity.ActivityEvent` dict
into the on-the-wire schema that a downstream system understands. The default
:class:`ECSMapper` produces Elastic Common Schema 8.x — the de-facto lingua
franca for Elastic, Sentinel (via the Log Ingestion API + DCR), Wazuh, and a
growing number of OSS SIEMs. Additional mappers (CEF, OCSF, Splunk CIM) plug
in here without touching the dispatch path.
"""

from aigis.forwarders.schema.ecs import ECSMapper, EventMapper

__all__ = ["ECSMapper", "EventMapper"]
