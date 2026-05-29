"""Generic HTTPS / HTTP JSON forwarder.

A minimal stdlib-only sink suitable for:

* Splunk HTTP Event Collector (HEC) — point ``url`` at
  ``https://<splunk>:8088/services/collector`` and set
  ``Authorization: Splunk <token>`` in ``headers``,
* Datadog Logs API (``https://http-intake.logs.datadoghq.com/api/v2/logs``),
* Azure Sentinel via a custom Logs Ingestion endpoint (DCR-backed),
* generic in-house SIEM ingest endpoints that accept newline-delimited JSON
  or a JSON array body.

For deployments that want a vendor-specific client (cosignature, regional
endpoints, OAuth refresh) a thin subclass adds ~20 LOC; the base does the
heavy lifting.
"""

from __future__ import annotations

import gzip
import io
import json
import logging
import time
import urllib.error
import urllib.request
from collections.abc import Mapping
from typing import Literal

from aigis.forwarders.base import LogForwarder

_log = logging.getLogger("aigis.forwarders.http")

# Conservative retry policy. SIEMs prefer steady drip over thundering retries.
_DEFAULT_RETRIES = 2
_DEFAULT_BACKOFF = 0.5  # seconds; doubled per attempt


class HTTPJsonForwarder(LogForwarder):
    """POST batched events as JSON to an HTTPS endpoint.

    Parameters
    ----------
    url:
        Full destination URL. HTTPS is recommended; the forwarder accepts
        ``http://`` for in-VPC SIEM endpoints but logs a one-time warning.
    headers:
        Static headers (auth tokens, tenant IDs). Sensitive headers are
        never logged.
    body_format:
        ``"ndjson"`` (default) writes one JSON object per line — the format
        Splunk HEC's ``/event/raw`` and Elastic ``_bulk`` accept. ``"array"``
        sends a single JSON list — what most generic SIEM ingest APIs want.
    gzip_payload:
        gzip-compress the request body. Recommended for high-volume sinks.
    timeout:
        Per-request timeout in seconds.
    retries:
        Number of retries on transport / 5xx errors before giving up the
        batch. 4xx errors are not retried (they indicate misconfiguration
        and the local JSONL tier still has the event).
    """

    def __init__(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        body_format: Literal["ndjson", "array"] = "ndjson",
        gzip_payload: bool = False,
        timeout: float = 5.0,
        retries: int = _DEFAULT_RETRIES,
        backoff: float = _DEFAULT_BACKOFF,
        **forwarder_kwargs: object,
    ) -> None:
        if not url.startswith(("http://", "https://")):
            raise ValueError(f"HTTPJsonForwarder url must be http(s); got {url!r}")
        if url.startswith("http://"):
            _log.warning(
                "HTTPJsonForwarder: %s is not HTTPS; SIEM traffic is sensitive — "
                "use TLS in production",
                url,
            )

        self._url = url
        self._headers: dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": "aigis-forwarder/1",
        }
        if headers:
            self._headers.update(headers)
        if gzip_payload:
            self._headers["Content-Encoding"] = "gzip"

        self._body_format = body_format
        self._gzip = gzip_payload
        self._timeout = timeout
        self._retries = max(0, retries)
        self._backoff = max(0.0, backoff)

        super().__init__(**forwarder_kwargs)  # type: ignore[arg-type]

    # -- LogForwarder hook --------------------------------------------------

    def _ship(self, batch: list[dict]) -> None:
        if not batch:
            return

        body = self._encode(batch)
        last_exc: Exception | None = None

        for attempt in range(self._retries + 1):
            try:
                self._post(body)
                return
            except urllib.error.HTTPError as e:
                # 4xx: don't retry — config bug. 5xx / network: retry.
                if 400 <= e.code < 500:
                    _log.error(
                        "HTTPJsonForwarder: %s returned %d; not retrying. "
                        "Events remain in local JSONL tier.",
                        self._url,
                        e.code,
                    )
                    raise
                last_exc = e
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last_exc = e

            if attempt < self._retries:
                time.sleep(self._backoff * (2**attempt))

        assert last_exc is not None
        raise last_exc

    # -- Internal -----------------------------------------------------------

    def _encode(self, batch: list[dict]) -> bytes:
        if self._body_format == "array":
            payload = json.dumps(batch, ensure_ascii=False, default=str).encode("utf-8")
        else:  # ndjson
            buf = io.StringIO()
            for doc in batch:
                buf.write(json.dumps(doc, ensure_ascii=False, default=str))
                buf.write("\n")
            payload = buf.getvalue().encode("utf-8")

        if self._gzip:
            gz = io.BytesIO()
            with gzip.GzipFile(fileobj=gz, mode="wb") as f:
                f.write(payload)
            payload = gz.getvalue()
        return payload

    def _post(self, body: bytes) -> None:
        req = urllib.request.Request(  # noqa: S310 — URL is operator-supplied config
            self._url, data=body, headers=self._headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
            # Drain the response so the connection can be reused / closed cleanly.
            resp.read()
