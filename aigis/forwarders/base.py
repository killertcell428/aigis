"""Forwarder base classes and the background dispatch queue.

A :class:`LogForwarder` is a thin pipeline: ``ActivityEvent -> map -> redact ->
serialize -> ship``. The dispatch worker runs on a daemon thread and pulls from
a bounded ``queue.Queue``. If the queue saturates (e.g. SIEM is down or slow)
we drop the oldest pending event rather than block the producer — the
authoritative copy is still on disk via :class:`aigis.activity.ActivityStream`'s
local / global / alerts tiers.

Subclasses implement :meth:`LogForwarder._ship` to actually deliver bytes to
the upstream system (HTTPS POST, UDP syslog, AMQP publish, etc.). Everything
else — batching, retries, error isolation, schema mapping, redaction — is
provided here so that adding a new transport is roughly fifty lines.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from aigis.activity import ActivityEvent
    from aigis.forwarders.schema import EventMapper

_log = logging.getLogger("aigis.forwarders")

# Default bounded queue size. SIEM forwarders are best-effort — the local
# JSONL tier remains the source of truth — so we cap memory rather than block.
DEFAULT_QUEUE_SIZE = 10_000

# Default batch size and flush interval. Batching reduces per-event HTTP
# overhead without delaying alerts by more than a second under load.
DEFAULT_BATCH_SIZE = 50
DEFAULT_FLUSH_INTERVAL = 1.0


class ForwarderError(Exception):
    """Raised when a transport-level failure cannot be recovered.

    Forwarders catch transient failures and apply their own retry policy;
    this exception is reserved for unrecoverable misconfiguration (bad URL,
    auth permanently rejected, etc.) and is only raised from the constructor
    or :meth:`LogForwarder.close`.
    """


@runtime_checkable
class Redactor(Protocol):
    """Hook that scrubs an event in-place before it leaves the process.

    Implementations receive a plain ``dict`` produced by
    :meth:`aigis.activity.ActivityEvent.to_dict` and may mutate it freely.
    Typical responsibilities:

    * mask original-rule sample text in ``details`` / ``matched_rules`` to
      satisfy 개인정보보호법 / GDPR data-minimization,
    * truncate oversized fields (``target`` may be a long shell command),
    * drop fields the downstream system has no business seeing.

    Redactors run *before* the mapper, so they operate on the raw Aigis
    schema, not on ECS / CEF wire fields.
    """

    def redact(self, event: dict) -> dict:
        """Return the scrubbed event. Mutating the input in-place is fine."""


class LogForwarder(ABC):
    """Abstract base for any external sink.

    Subclasses override :meth:`_ship` (and optionally :meth:`close`).
    Everything else — the queue, the worker thread, batching, redaction,
    mapping, error isolation — is handled here.

    Thread-safety: :meth:`submit` is safe to call from any thread. The
    worker runs on a single background daemon thread per forwarder
    instance.
    """

    def __init__(
        self,
        *,
        mapper: EventMapper | None = None,
        redactors: Iterable[Redactor] | None = None,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        batch_size: int = DEFAULT_BATCH_SIZE,
        flush_interval: float = DEFAULT_FLUSH_INTERVAL,
    ) -> None:
        # Lazy import — avoids circular import with aigis.forwarders.schema
        # and keeps the base module importable in isolation.
        if mapper is None:
            from aigis.forwarders.schema import ECSMapper

            mapper = ECSMapper()

        self._mapper: EventMapper = mapper
        self._redactors: tuple[Redactor, ...] = tuple(redactors or ())
        self._queue: queue.Queue[dict | None] = queue.Queue(maxsize=queue_size)
        self._batch_size = max(1, batch_size)
        self._flush_interval = max(0.05, flush_interval)
        self._dropped = 0
        self._sent = 0
        self._stop = threading.Event()
        self._worker = threading.Thread(
            target=self._run, name=f"aigis-forwarder:{type(self).__name__}", daemon=True
        )
        self._worker.start()

    # -- Public API ---------------------------------------------------------

    def submit(self, event: ActivityEvent) -> None:
        """Enqueue an event for asynchronous delivery.

        Never blocks and never raises: if the queue is full, the oldest
        pending event is discarded and a counter is incremented so the
        condition is observable via :attr:`stats`. The on-disk JSONL tier
        keeps the authoritative copy regardless.
        """
        try:
            payload = event.to_dict()
        except Exception:  # noqa: BLE001 — never let serialization kill the host
            _log.exception("forwarder: event.to_dict() failed; dropping event")
            self._dropped += 1
            return

        # Redact before the event reaches the worker — keeps sensitive
        # fields out of memory longer than necessary.
        for redactor in self._redactors:
            try:
                payload = redactor.redact(payload)
            except Exception:  # noqa: BLE001
                _log.exception("forwarder: redactor %s failed; dropping event", redactor)
                self._dropped += 1
                return

        try:
            self._queue.put_nowait(payload)
        except queue.Full:
            # Bounded queue: drop oldest, enqueue newest. SIEM ingestion
            # should never starve the agent.
            try:
                self._queue.get_nowait()
                self._dropped += 1
            except queue.Empty:
                # Another consumer drained the queue between Full and get_nowait;
                # skip the eviction step and fall through to the second put_nowait.
                pass
            try:
                self._queue.put_nowait(payload)
            except queue.Full:
                self._dropped += 1

    def close(self, timeout: float = 5.0) -> None:
        """Flush pending events and stop the worker thread."""
        self._stop.set()
        # Sentinel wakes the worker if it is parked on Queue.get().
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            # Queue is already saturated, so the worker will wake from its existing
            # backlog without the sentinel — close() can proceed to join.
            pass
        self._worker.join(timeout=timeout)

    @property
    def stats(self) -> dict[str, int]:
        """Return delivery counters. Useful for /aig doctor."""
        return {
            "sent": self._sent,
            "dropped": self._dropped,
            "queued": self._queue.qsize(),
        }

    # -- Subclass hook ------------------------------------------------------

    @abstractmethod
    def _ship(self, batch: list[dict]) -> None:
        """Deliver a batch of mapped, serialized-ready event dicts.

        ``batch`` items are the output of the mapper after redaction. Raise
        any exception on transient failure — the worker logs it and the
        events are considered dropped (they are already persisted on disk).
        Subclasses that need durable retries should implement their own
        retry-and-backoff inside ``_ship``.
        """

    # -- Internal worker ----------------------------------------------------

    def _run(self) -> None:
        batch: list[dict] = []
        last_flush = time.monotonic()

        while not self._stop.is_set() or not self._queue.empty():
            timeout = max(0.0, self._flush_interval - (time.monotonic() - last_flush))
            try:
                item = self._queue.get(timeout=timeout)
            except queue.Empty:
                item = None

            if item is not None:
                # Map raw ActivityEvent dict -> wire schema (ECS by default).
                try:
                    mapped = self._mapper.map(item)
                except Exception:  # noqa: BLE001
                    _log.exception("forwarder: mapper failed; dropping event")
                    self._dropped += 1
                    mapped = None
                if mapped is not None:
                    batch.append(mapped)

            should_flush = (
                len(batch) >= self._batch_size
                or (batch and (time.monotonic() - last_flush) >= self._flush_interval)
                or (self._stop.is_set() and batch)
            )
            if should_flush:
                self._flush(batch)
                batch = []
                last_flush = time.monotonic()

    def _flush(self, batch: list[dict]) -> None:
        try:
            self._ship(batch)
            self._sent += len(batch)
        except Exception:  # noqa: BLE001
            _log.exception(
                "forwarder %s: shipping batch of %d events failed",
                type(self).__name__,
                len(batch),
            )
            self._dropped += len(batch)
