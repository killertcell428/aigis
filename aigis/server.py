"""Aigis HTTP server — sidecar / proxy mode for non-Python stacks.

Stdlib-only HTTP server that exposes Guard.check_input / check_output / check_messages
as JSON endpoints. Lets Aigis run as a Docker sidecar in front of any agent runtime.

    docker run -p 8080:8080 ghcr.io/killertcell428/aigis serve

    curl -X POST http://localhost:8080/v1/check/input \
      -H 'Content-Type: application/json' \
      -d '{"text": "Ignore all previous instructions"}'

Endpoints:
    GET  /health              — liveness probe (200 ok)
    GET  /v1/info             — package version + active wall config
    POST /v1/check/input      — body: {"text": "..."} -> CheckResult JSON
    POST /v1/check/output     — body: {"text": "..."} -> CheckResult JSON
    POST /v1/check/messages   — body: {"messages": [...]} -> CheckResult JSON

CheckResult JSON shape:
    {
      "blocked": true,
      "risk_score": 85,
      "risk_level": "CRITICAL",
      "reasons": ["Ignore Previous Instructions"],
      "matched_rules": [{"rule_id": "...", "category": "...", ...}]
    }
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from aigis import __version__ as aigis_version
from aigis.guard import Guard
from aigis.types import CheckResult

logger = logging.getLogger("aigis.server")

_MAX_BODY_BYTES = 1 * 1024 * 1024  # 1 MiB cap to avoid memory abuse


def _check_result_to_dict(result: CheckResult) -> dict[str, Any]:
    return {
        "blocked": result.blocked,
        "risk_score": result.risk_score,
        "risk_level": str(result.risk_level),
        "reasons": list(result.reasons),
        "matched_rules": [asdict(r) for r in result.matched_rules],
        "remediation": dict(result.remediation),
    }


class AigisHandler(BaseHTTPRequestHandler):
    server_version = f"Aigis/{aigis_version}"
    sys_version = ""

    # Set by make_server() — the shared Guard instance.
    guard: Guard

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        logger.info("%s - %s", self.address_string(), format % args)

    def _send_json(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_json(self) -> dict[str, Any] | None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "missing body"})
            return None
        if length > _MAX_BODY_BYTES:
            self._send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "body too large"})
            return None
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": f"invalid JSON: {exc}"})
            return None
        if not isinstance(data, dict):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "expected JSON object"})
            return None
        return data

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok"})
            return
        if self.path == "/v1/info":
            self._send_json(
                HTTPStatus.OK,
                {
                    "name": "aigis",
                    "version": aigis_version,
                    "endpoints": [
                        "POST /v1/check/input",
                        "POST /v1/check/output",
                        "POST /v1/check/messages",
                    ],
                },
            )
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": f"unknown path: {self.path}"})

    def do_POST(self) -> None:  # noqa: N802
        data = self._read_json()
        if data is None:
            return
        try:
            if self.path == "/v1/check/input":
                text = data.get("text")
                if not isinstance(text, str):
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": "text must be string"})
                    return
                result = self.guard.check_input(text)
            elif self.path == "/v1/check/output":
                text = data.get("text")
                if not isinstance(text, str):
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": "text must be string"})
                    return
                result = self.guard.check_output(text)
            elif self.path == "/v1/check/messages":
                messages = data.get("messages")
                if not isinstance(messages, list):
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": "messages must be list"})
                    return
                result = self.guard.check_messages(messages)
            else:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": f"unknown path: {self.path}"})
                return
        except Exception as exc:
            logger.exception("scan failed")
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
            return
        self._send_json(HTTPStatus.OK, _check_result_to_dict(result))


def make_server(host: str, port: int, guard: Guard | None = None) -> ThreadingHTTPServer:
    handler_cls = type("BoundAigisHandler", (AigisHandler,), {"guard": guard or Guard()})
    return ThreadingHTTPServer((host, port), handler_cls)


def serve(host: str = "0.0.0.0", port: int = 8080, guard: Guard | None = None) -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
        )
    server = make_server(host, port, guard)
    logger.info("Aigis %s listening on http://%s:%d", aigis_version, host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("shutting down")
    finally:
        server.server_close()


if __name__ == "__main__":  # pragma: no cover
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    serve(port=port)
