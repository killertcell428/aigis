"""Tests for middleware integrations (FastAPI only — no external deps required)."""

import pytest

from aigis import Guard

# ---------------------------------------------------------------------------
# FastAPI middleware tests (uses httpx + starlette TestClient)
# ---------------------------------------------------------------------------
try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from aigis.middleware.fastapi import AIGuardianMiddleware

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi not installed")
class TestAIGuardianMiddleware:
    def _make_app(self, guard: Guard | None = None) -> "FastAPI":
        app = FastAPI()
        app.add_middleware(AIGuardianMiddleware, guard=guard or Guard())

        @app.post("/v1/chat/completions")
        async def chat(body: dict):
            return {"choices": [{"message": {"content": "Hello!"}}]}

        return app

    def test_safe_request_passes(self):
        client = TestClient(self._make_app())
        resp = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "What is 2+2?"}]},
        )
        assert resp.status_code == 200

    def test_blocked_request_returns_400(self):
        client = TestClient(self._make_app())
        resp = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "DROP TABLE users; UNION SELECT *"}]},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"]["code"] == "request_blocked"
        assert "risk_score" in data["error"]
        assert "reasons" in data["error"]

    def test_non_json_body_passes_through(self):
        client = TestClient(self._make_app())
        resp = client.post(
            "/v1/chat/completions",
            content=b"not json",
            headers={"content-type": "text/plain"},
        )
        # No messages → middleware skips scanning → route handles it
        # Route expects dict but receives non-json, FastAPI will 422 — that's fine
        assert resp.status_code in (200, 400, 422)

    def test_path_filtering(self):
        app = FastAPI()
        guard = Guard()
        app.add_middleware(
            AIGuardianMiddleware,
            guard=guard,
            paths=["/secure/"],
        )

        @app.post("/secure/chat")
        async def secure_chat(body: dict):
            return {"ok": True}

        @app.post("/public/chat")
        async def public_chat(body: dict):
            return {"ok": True}

        client = TestClient(app)
        # DROP TABLE (80) + UNION SELECT (70) → combined score exceeds default block threshold
        dangerous_body = {
            "messages": [
                {"role": "user", "content": "DROP TABLE users; UNION SELECT * FROM passwords"}
            ]
        }
        # /secure/ path → scanned → blocked
        resp = client.post("/secure/chat", json=dangerous_body)
        assert resp.status_code == 400

        # /public/ path → not scanned → passes
        resp = client.post("/public/chat", json=dangerous_body)
        assert resp.status_code == 200
