"""FastAPI middleware for aigis.

Usage::

    from fastapi import FastAPI
    from aigis import Guard
    from aigis.middleware.fastapi import AIGuardianMiddleware

    app = FastAPI()
    guard = Guard()
    app.add_middleware(AIGuardianMiddleware, guard=guard)

The middleware intercepts ``/chat/completions``-style endpoints,
scans the request body, and returns a 400 JSON error if blocked.
All other paths pass through unchanged.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from starlette.types import ASGIApp

    from aigis.guard import Guard

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse, Response
except ImportError as e:
    raise ImportError(
        "FastAPI/Starlette is required for AIGuardianMiddleware. "
        "Install it with: pip install 'aigis[fastapi]'"
    ) from e


class AIGuardianMiddleware(BaseHTTPMiddleware):
    """Starlette/FastAPI middleware that scans LLM request bodies.

    Intercepts any POST request whose body contains an OpenAI-style
    ``messages`` array. If the Guard blocks the request, returns HTTP 400
    with a structured error response before it reaches your route handler.

    Args:
        app: The ASGI application.
        guard: A configured :class:`~aigis.Guard` instance.
        check_output: Also scan LLM responses if ``True``. Defaults to ``False``
                      because response scanning requires buffering the response
                      body and may add latency.
        paths: Optional list of path prefixes to scan. Defaults to all POST paths.
    """

    def __init__(
        self,
        app: ASGIApp,
        guard: Guard,
        check_output: bool = False,
        paths: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.guard = guard
        self.check_output = check_output
        self.paths = paths

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if request.method == "POST" and self._should_scan(request.url.path):
            body_bytes = await request.body()

            # Re-inject body so downstream handlers can read it again.
            # Starlette's Request caches body bytes internally after the
            # first await, so subsequent request.body() calls return the
            # cached value. However, some ASGI servers or test clients
            # rely on the receive channel. We set the internal cache
            # explicitly to guarantee availability.
            request._body = body_bytes  # type: ignore[attr-defined]

            try:
                body = json.loads(body_bytes)
            except (json.JSONDecodeError, ValueError):
                body = {}

            messages = body.get("messages")
            if messages:
                result = self.guard.check_messages(messages)
                if result.blocked:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": {
                                "type": "guardian_policy_violation",
                                "code": "request_blocked",
                                "message": "Request blocked by Aigis security policy.",
                                "risk_score": result.risk_score,
                                "risk_level": result.risk_level.value,
                                "reasons": result.reasons,
                                "remediation": result.remediation,
                            }
                        },
                    )

        response: Response = await call_next(request)

        # Output scanning: if enabled, inspect the response body for data leaks
        if self.check_output and request.method == "POST" and self._should_scan(request.url.path):
            if hasattr(response, "body"):
                try:
                    resp_body = json.loads(response.body)
                    out_result = self.guard.check_response(resp_body)
                    if out_result.blocked:
                        return JSONResponse(
                            status_code=400,
                            content={
                                "error": {
                                    "type": "guardian_policy_violation",
                                    "code": "response_blocked",
                                    "message": "Response blocked by Aigis security policy.",
                                    "risk_score": out_result.risk_score,
                                    "risk_level": out_result.risk_level.value,
                                    "reasons": out_result.reasons,
                                    "remediation": out_result.remediation,
                                }
                            },
                        )
                except (json.JSONDecodeError, ValueError, AttributeError):
                    pass

        return response

    def _should_scan(self, path: str) -> bool:
        if self.paths is None:
            return True
        return any(path.startswith(p) for p in self.paths)
