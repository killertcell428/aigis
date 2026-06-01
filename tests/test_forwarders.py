"""Tests for aigis.forwarders.

Coverage:
  * ECS schema mapping (golden assertions on field structure & ECS enums)
  * HTTPS round-trip against an in-process http.server-based fake collector
  * Redactor protocol applied before mapping
  * Bounded queue degrades gracefully under saturation
  * ActivityStream.add_forwarder() wires events end-to-end without blocking
"""

from __future__ import annotations

import gzip
import io
import json
import tempfile
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest

from aigis.activity import ActivityEvent, ActivityStream
from aigis.forwarders import (
    ECSMapper,
    HTTPJsonForwarder,
    LogForwarder,
)
from aigis.forwarders.schema.ecs import ECS_VERSION

# ---------------------------------------------------------------------------
# Fake collector — minimal HTTP server we can introspect.
# ---------------------------------------------------------------------------


class _Collector:
    """An in-process HTTP collector that records every request body."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self.fail_next_n = 0
        self.status_override = 200

        collector = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args: Any, **_kwargs: Any) -> None:  # silence
                return

            def do_POST(self) -> None:  # noqa: N802 — BaseHTTPRequestHandler API
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
                if self.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                with collector._lock:
                    collector.requests.append(
                        {
                            "path": self.path,
                            "headers": dict(self.headers),
                            "body": raw.decode("utf-8"),
                        }
                    )
                    if collector.fail_next_n > 0:
                        collector.fail_next_n -= 1
                        self.send_response(503)
                        self.end_headers()
                        return
                self.send_response(collector.status_override)
                self.end_headers()
                self.wfile.write(b"ok")

        self._handler = Handler
        self._server = HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self._server.server_port
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/ingest"

    def shutdown(self) -> None:
        self._server.shutdown()
        self._server.server_close()


@pytest.fixture
def collector() -> Iterator[_Collector]:
    c = _Collector()
    try:
        yield c
    finally:
        c.shutdown()


# ---------------------------------------------------------------------------
# ECS mapper — golden tests
# ---------------------------------------------------------------------------


class TestECSMapper:
    def test_alert_event_kind(self) -> None:
        e = ActivityEvent(
            action="shell:exec",
            target="rm -rf /",
            policy_decision="deny",
            risk_score=95,
            risk_level="critical",
            matched_rules=["dangerous_commands"],
            owasp_refs=["CWE-78"],
            remediation_hints=["Use targeted deletion"],
            policy_rule_id="P-001",
            user_id="alice",
        )
        doc = ECSMapper().map(e.to_dict())

        assert doc["ecs"]["version"] == ECS_VERSION
        assert doc["event"]["kind"] == "alert"
        assert doc["event"]["category"] == ["process"]
        assert doc["event"]["outcome"] == "failure"
        assert doc["event"]["severity"] == 7
        assert doc["event"]["risk_score"] == 95
        assert doc["event"]["action"] == "shell:exec"
        assert doc["event"]["dataset"] == "aigis.activity"
        assert doc["user"]["name"] == "alice"
        assert doc["process"]["command_line"] == "rm -rf /"
        assert doc["rule"]["name"] == "dangerous_commands"
        assert doc["rule"]["id"] == "P-001"
        # Aigis-native fields preserved verbatim
        assert doc["aigis"]["policy"]["decision"] == "deny"
        assert doc["aigis"]["matched_rules"] == ["dangerous_commands"]
        assert doc["aigis"]["owasp_refs"] == ["CWE-78"]

    def test_safe_event_kind(self) -> None:
        e = ActivityEvent(action="file:read", target="readme.md", risk_score=0)
        doc = ECSMapper().map(e.to_dict())
        assert doc["event"]["kind"] == "event"
        assert doc["event"]["outcome"] == "success"
        assert doc["event"]["category"] == ["file"]

    def test_review_outcome_is_unknown(self) -> None:
        e = ActivityEvent(action="shell:exec", target="ls", policy_decision="review")
        doc = ECSMapper().map(e.to_dict())
        assert doc["event"]["outcome"] == "unknown"
        assert doc["event"]["kind"] == "alert"

    def test_namespace_emits_data_stream(self) -> None:
        e = ActivityEvent(action="file:read", target="x")
        doc = ECSMapper(namespace="tenant-a").map(e.to_dict())
        assert doc["data_stream"] == {
            "type": "logs",
            "dataset": "aigis.activity",
            "namespace": "tenant-a",
        }

    def test_none_fields_pruned(self) -> None:
        e = ActivityEvent(action="file:read", target="x")
        doc = ECSMapper().map(e.to_dict())
        # user.name is unset (synthetic ActivityEvent fills user_id from OS,
        # but it's never literally None). Confirm None pruning works by
        # checking that an explicitly-empty optional is gone.
        assert "reason" not in doc["event"]
        assert "suggested_fix" not in doc["aigis"]

    def test_outcome_error_maps_to_failure(self) -> None:
        """ActivityEvent with policy_decision='error' (e.g. scan crash) must
        surface as ECS event.outcome='failure' so SOC dashboards group it
        with denies rather than dropping it as 'unknown'."""
        e = ActivityEvent(action="shell:exec", target="ls", policy_decision="error")
        doc = ECSMapper().map(e.to_dict())
        assert doc["event"]["outcome"] == "failure"
        # Original decision verb preserved verbatim for analysts who need
        # to distinguish 'deny' (policy blocked) from 'error' (scan failed).
        assert doc["aigis"]["policy"]["decision"] == "error"

    def test_event_kind_alert_triggered_by_event_type(self) -> None:
        """event.kind='alert' must be raised even when risk_score is low and
        decision is allow, if event_type indicates a scan/block event."""
        e = ActivityEvent(
            action="scan:input",
            target="x",
            event_type="scan_alert",
            risk_score=0,
            policy_decision="allow",
        )
        doc = ECSMapper().map(e.to_dict())
        assert doc["event"]["kind"] == "alert"


# ---------------------------------------------------------------------------
# HTTP forwarder — round-trip
# ---------------------------------------------------------------------------


class TestHTTPJsonForwarder:
    def test_ndjson_round_trip(self, collector: _Collector) -> None:
        fwd = HTTPJsonForwarder(
            collector.url,
            headers={"Authorization": "Bearer test"},
            flush_interval=0.05,
            batch_size=2,
        )
        try:
            fwd.submit(ActivityEvent(action="shell:exec", target="ls", user_id="alice"))
            fwd.submit(ActivityEvent(action="file:read", target="x.py", user_id="alice"))
            _wait_for(lambda: len(collector.requests) >= 1, timeout=15.0)
        finally:
            fwd.close()

        assert len(collector.requests) >= 1
        body = collector.requests[0]["body"].strip().splitlines()
        docs = [json.loads(line) for line in body]
        actions = {d["event"]["action"] for d in docs}
        assert actions == {"shell:exec", "file:read"}
        assert collector.requests[0]["headers"]["Authorization"] == "Bearer test"

    def test_array_body_format(self, collector: _Collector) -> None:
        fwd = HTTPJsonForwarder(
            collector.url,
            body_format="array",
            flush_interval=0.05,
            batch_size=1,
        )
        try:
            fwd.submit(ActivityEvent(action="shell:exec", target="ls"))
            _wait_for(lambda: len(collector.requests) >= 1, timeout=15.0)
        finally:
            fwd.close()

        body = json.loads(collector.requests[0]["body"])
        assert isinstance(body, list)
        assert body[0]["event"]["action"] == "shell:exec"

    def test_gzip_payload(self, collector: _Collector) -> None:
        fwd = HTTPJsonForwarder(
            collector.url,
            gzip_payload=True,
            flush_interval=0.05,
            batch_size=1,
        )
        try:
            fwd.submit(ActivityEvent(action="shell:exec", target="ls"))
            _wait_for(lambda: len(collector.requests) >= 1, timeout=15.0)
        finally:
            fwd.close()

        assert collector.requests[0]["headers"]["Content-Encoding"] == "gzip"
        # Handler already decompressed for us; body should now be plain ndjson.
        json.loads(collector.requests[0]["body"].strip().splitlines()[0])

    def test_retry_on_5xx(self, collector: _Collector) -> None:
        collector.fail_next_n = 2  # first two attempts return 503
        fwd = HTTPJsonForwarder(
            collector.url,
            flush_interval=0.05,
            batch_size=1,
            retries=3,
            backoff=0.05,
        )
        try:
            fwd.submit(ActivityEvent(action="shell:exec", target="ls"))
            _wait_for(lambda: fwd.stats["sent"] >= 1, timeout=15.0)
        finally:
            fwd.close()

        # 2 failures + 1 success = 3 requests recorded
        assert len(collector.requests) == 3
        assert fwd.stats["sent"] == 1
        assert fwd.stats["dropped"] == 0

    def test_4xx_not_retried(self, collector: _Collector) -> None:
        """4xx responses indicate misconfiguration; retrying amplifies the
        bug and clutters the SIEM-side logs. The local JSONL tier already
        has the event, so we drop and move on."""
        collector.status_override = 401
        fwd = HTTPJsonForwarder(
            collector.url,
            flush_interval=0.05,
            batch_size=1,
            retries=3,  # would retry on 5xx, must not on 4xx
            backoff=0.05,
        )
        try:
            fwd.submit(ActivityEvent(action="shell:exec", target="ls"))
            _wait_for(lambda: fwd.stats["dropped"] >= 1, timeout=15.0)
            # Give the worker enough time to attempt any (incorrect) retry
            # so we can prove it did not happen.
            time.sleep(0.5)
        finally:
            fwd.close()

        assert len(collector.requests) == 1, (
            f"4xx must not retry; got {len(collector.requests)} requests"
        )
        assert fwd.stats["sent"] == 0
        assert fwd.stats["dropped"] >= 1

    def test_rejects_non_http_url(self) -> None:
        with pytest.raises(ValueError):
            HTTPJsonForwarder("ftp://example.com/ingest")


# ---------------------------------------------------------------------------
# Redactor protocol
# ---------------------------------------------------------------------------


class _MaskTarget:
    """Test redactor that masks the `target` field."""

    def redact(self, event: dict) -> dict:
        event["target"] = "<redacted>"
        return event


class _StripDetails:
    def redact(self, event: dict) -> dict:
        event.pop("details", None)
        return event


class TestRedactor:
    def test_redactor_runs_before_mapping(self, collector: _Collector) -> None:
        fwd = HTTPJsonForwarder(
            collector.url,
            redactors=[_MaskTarget()],
            flush_interval=0.05,
            batch_size=1,
        )
        try:
            fwd.submit(ActivityEvent(action="shell:exec", target="rm -rf /etc"))
            _wait_for(lambda: len(collector.requests) >= 1, timeout=15.0)
        finally:
            fwd.close()

        doc = json.loads(collector.requests[0]["body"].strip().splitlines()[0])
        assert doc["process"]["command_line"] == "<redacted>"

    def test_chained_redactors_apply_in_order(self, collector: _Collector) -> None:
        """Multiple redactors run in registration order; each sees the
        output of the previous one. Required to make compliance-preset
        stacking (e.g. PIPA preset + project-specific overlay) predictable."""
        fwd = HTTPJsonForwarder(
            collector.url,
            # First strips `details`, second masks `target`. After both run,
            # the event should have neither `details` nor the original target.
            redactors=[_StripDetails(), _MaskTarget()],
            flush_interval=0.05,
            batch_size=1,
        )
        try:
            fwd.submit(
                ActivityEvent(
                    action="shell:exec",
                    target="rm -rf /etc",
                    details={"secret": "should-not-ship"},
                )
            )
            _wait_for(lambda: len(collector.requests) >= 1, timeout=15.0)
        finally:
            fwd.close()

        doc = json.loads(collector.requests[0]["body"].strip().splitlines()[0])
        assert doc["process"]["command_line"] == "<redacted>"
        # _StripDetails removed `details` from the raw event, so the
        # mapped aigis.details should be the empty default `{}`.
        assert doc["aigis"]["details"] == {}


# ---------------------------------------------------------------------------
# Bounded queue: graceful degradation
# ---------------------------------------------------------------------------


class _BlackHole(LogForwarder):
    """Forwarder that never delivers — used to test queue overflow."""

    def __init__(self) -> None:
        self.shipped = 0
        super().__init__(queue_size=4, batch_size=2, flush_interval=10.0)

    def _ship(self, batch: list[dict]) -> None:
        # Block long enough that the producer fills the queue.
        time.sleep(60)


class TestBoundedQueue:
    def test_drops_oldest_when_full(self) -> None:
        fwd = _BlackHole()
        try:
            for i in range(100):
                fwd.submit(ActivityEvent(action="file:read", target=f"f{i}"))
            # queue cap is 4, batch_size 2 -> worker may have drained ~2 into
            # an in-flight batch before blocking. So queue + dropped should
            # account for everything submitted minus what's in the worker.
            assert fwd.stats["dropped"] > 0
            assert fwd.stats["queued"] <= 4
        finally:
            fwd.close(timeout=0.1)


# ---------------------------------------------------------------------------
# Shutdown — close() must flush pending events, not drop them
# ---------------------------------------------------------------------------


class _SyncCollector(LogForwarder):
    """Forwarder that records ship() calls in-process — no HTTP server overhead
    so close() drain timing is deterministic."""

    def __init__(self, *, flush_interval: float = 60.0) -> None:
        self.shipped: list[dict] = []
        super().__init__(queue_size=100, batch_size=10, flush_interval=flush_interval)

    def _ship(self, batch: list[dict]) -> None:
        self.shipped.extend(batch)


class TestForwarderShutdown:
    def test_close_flushes_pending_batch(self) -> None:
        """close() must drain the queue and ship in-flight batches.
        Without this guarantee, a graceful agent shutdown silently loses
        the last seconds of audit signal — exactly when an incident is
        most likely to be unfolding."""
        # flush_interval is huge (60s) so the worker would NEVER flush on
        # its own within the test timeout. Only close() can drain it.
        fwd = _SyncCollector(flush_interval=60.0)
        for i in range(3):
            fwd.submit(ActivityEvent(action="file:read", target=f"f{i}"))

        # Nothing shipped yet — batch_size 10 not reached, interval not hit.
        assert fwd.shipped == []

        fwd.close(timeout=2.0)

        # close() must have drained all 3 events.
        assert len(fwd.shipped) == 3
        actions = {e.get("event", {}).get("action") for e in fwd.shipped}
        assert actions == {"file:read"}


# ---------------------------------------------------------------------------
# ActivityStream integration
# ---------------------------------------------------------------------------


class TestActivityStreamForwarderIntegration:
    def test_event_reaches_forwarder(self, collector: _Collector) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            stream = ActivityStream(log_dir=tmpdir, enable_global=False, enable_alerts=False)
            fwd = HTTPJsonForwarder(collector.url, flush_interval=0.05, batch_size=1)
            stream.add_forwarder(fwd)
            try:
                stream.record(ActivityEvent(action="shell:exec", target="ls"))
                _wait_for(lambda: len(collector.requests) >= 1, timeout=15.0)
            finally:
                stream.close_forwarders(timeout=1.0)

            # Local JSONL tier still written
            events = stream.query(days=1)
            assert len(events) == 1
            # Forwarder also delivered
            doc = json.loads(collector.requests[0]["body"].strip().splitlines()[0])
            assert doc["event"]["action"] == "shell:exec"

    def test_broken_forwarder_does_not_block_record(self) -> None:
        class Boom:
            def submit(self, _event: object) -> None:
                raise RuntimeError("siem on fire")

        with tempfile.TemporaryDirectory() as tmpdir:
            stream = ActivityStream(log_dir=tmpdir, enable_global=False, enable_alerts=False)
            stream._forwarders.append(Boom())  # type: ignore[arg-type]
            # Must not raise even though the forwarder explodes
            stream.record(ActivityEvent(action="shell:exec", target="ls"))
            assert len(stream.query(days=1)) == 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _wait_for(predicate: Any, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError(f"timed out waiting for {predicate}")


# Used only to satisfy mypy/ruff for the silently-imported io
_ = io
