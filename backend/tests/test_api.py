"""Integration tests for API endpoints."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.models.policy import Policy
from app.models.tenant import Tenant
from app.models.user import User


@pytest.mark.asyncio
class TestHealthCheck:
    async def test_health(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
class TestAdminAuth:
    async def test_login_success(
        self, client: AsyncClient, admin_user: User
    ):
        resp = await client.post(
            "/api/v1/admin/auth/login",
            json={"email": admin_user.email, "password": "password123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(
        self, client: AsyncClient, admin_user: User
    ):
        resp = await client.post(
            "/api/v1/admin/auth/login",
            json={"email": admin_user.email, "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    async def test_get_me(
        self, client: AsyncClient, admin_user: User, admin_token: str
    ):
        resp = await client.get(
            "/api/v1/admin/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == admin_user.email

    async def test_get_me_unauthorized(self, client: AsyncClient):
        resp = await client.get("/api/v1/admin/auth/me")
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestPoliciesAPI:
    async def test_list_policies(
        self,
        client: AsyncClient,
        admin_token: str,
        policy: Policy,
    ):
        resp = await client.get(
            "/api/v1/policies/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert any(p["id"] == str(policy.id) for p in data)

    async def test_create_policy(
        self, client: AsyncClient, admin_token: str
    ):
        resp = await client.post(
            "/api/v1/policies/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Strict Policy",
                "auto_allow_threshold": 10,
                "auto_block_threshold": 50,
                "review_sla_minutes": 15,
                "sla_fallback": "block",
                "custom_rules": [],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Strict Policy"
        assert data["auto_block_threshold"] == 50

    async def test_reviewer_cannot_create_policy(
        self, client: AsyncClient, reviewer_token: str
    ):
        resp = await client.post(
            "/api/v1/policies/",
            headers={"Authorization": f"Bearer {reviewer_token}"},
            json={"name": "Hack", "auto_allow_threshold": 0, "auto_block_threshold": 100},
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestReviewAPI:
    async def test_list_review_queue(
        self, client: AsyncClient, reviewer_token: str
    ):
        resp = await client.get(
            "/api/v1/review/queue",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_list_review_queue_unauthorized(self, client: AsyncClient):
        resp = await client.get("/api/v1/review/queue")
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestAuditAPI:
    async def test_list_audit_logs(
        self, client: AsyncClient, reviewer_token: str
    ):
        resp = await client.get(
            "/api/v1/audit/logs",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
