"""Tests for review queue service."""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request import Request
from app.models.review import ReviewItem
from app.models.tenant import Tenant
from app.models.user import User
from app.review.service import (
    enqueue_for_review,
    handle_sla_timeouts,
    process_review_decision,
)


def make_request(tenant_id: uuid.UUID) -> Request:
    return Request(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        model="gpt-4o",
        messages=[{"role": "user", "content": "Test"}],
        input_risk_score=50,
        input_risk_level="medium",
        input_matched_rules=[],
        status="pending",
    )


@pytest.mark.asyncio
class TestEnqueueForReview:
    async def test_creates_review_item(self, db_session: AsyncSession, tenant: Tenant):
        req = make_request(tenant.id)
        db_session.add(req)
        await db_session.flush()

        item = await enqueue_for_review(db_session, req, sla_minutes=30)

        assert item.request_id == req.id
        assert item.status == "pending"
        assert req.status == "queued_for_review"
        assert item.sla_deadline > datetime.now(timezone.utc)

    async def test_sla_deadline_set_correctly(self, db_session: AsyncSession, tenant: Tenant):
        req = make_request(tenant.id)
        db_session.add(req)
        await db_session.flush()

        before = datetime.now(timezone.utc)
        item = await enqueue_for_review(db_session, req, sla_minutes=15)
        after = datetime.now(timezone.utc)

        expected_min = before + timedelta(minutes=14)
        expected_max = after + timedelta(minutes=16)
        assert expected_min < item.sla_deadline < expected_max


@pytest.mark.asyncio
class TestProcessReviewDecision:
    async def _setup_item(
        self, db_session: AsyncSession, tenant: Tenant
    ) -> tuple[Request, ReviewItem]:
        req = make_request(tenant.id)
        db_session.add(req)
        await db_session.flush()
        item = await enqueue_for_review(db_session, req, sla_minutes=30)
        return req, item

    async def test_approve(
        self, db_session: AsyncSession, tenant: Tenant, reviewer_user: User
    ):
        req, item = await self._setup_item(db_session, tenant)
        updated = await process_review_decision(
            db_session, item.id, reviewer_user.id, "approve"
        )
        assert updated.status == "approved"
        assert updated.decision == "approve"
        assert req.status == "allowed"

    async def test_reject(
        self, db_session: AsyncSession, tenant: Tenant, reviewer_user: User
    ):
        req, item = await self._setup_item(db_session, tenant)
        updated = await process_review_decision(
            db_session, item.id, reviewer_user.id, "reject", note="Policy violation"
        )
        assert updated.status == "rejected"
        assert req.status == "blocked"
        assert updated.reviewer_note == "Policy violation"

    async def test_escalate(
        self, db_session: AsyncSession, tenant: Tenant, reviewer_user: User
    ):
        req, item = await self._setup_item(db_session, tenant)
        updated = await process_review_decision(
            db_session, item.id, reviewer_user.id, "escalate"
        )
        assert updated.status == "escalated"
        assert req.status == "escalated"

    async def test_double_decision_raises(
        self, db_session: AsyncSession, tenant: Tenant, reviewer_user: User
    ):
        req, item = await self._setup_item(db_session, tenant)
        await process_review_decision(db_session, item.id, reviewer_user.id, "approve")
        with pytest.raises(ValueError, match="already"):
            await process_review_decision(
                db_session, item.id, reviewer_user.id, "reject"
            )

    async def test_nonexistent_item_raises(
        self, db_session: AsyncSession, reviewer_user: User
    ):
        with pytest.raises(ValueError, match="not found"):
            await process_review_decision(
                db_session, uuid.uuid4(), reviewer_user.id, "approve"
            )


@pytest.mark.asyncio
class TestSLATimeouts:
    async def test_timed_out_items_blocked(self, db_session: AsyncSession, tenant: Tenant):
        req = make_request(tenant.id)
        db_session.add(req)
        await db_session.flush()

        # Create item with past deadline
        past_deadline = datetime.now(timezone.utc) - timedelta(minutes=1)
        item = ReviewItem(
            id=uuid.uuid4(),
            request_id=req.id,
            status="pending",
            sla_deadline=past_deadline,
        )
        req.status = "queued_for_review"
        db_session.add(item)
        db_session.add(req)
        await db_session.flush()

        timed_out = await handle_sla_timeouts(db_session)

        assert len(timed_out) >= 1
        assert any(t.id == item.id for t in timed_out)
        assert item.status == "timed_out"
        assert req.status == "blocked"

    async def test_active_items_not_timed_out(self, db_session: AsyncSession, tenant: Tenant):
        req = make_request(tenant.id)
        db_session.add(req)
        await db_session.flush()

        # Create item with future deadline
        future_deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        item = ReviewItem(
            id=uuid.uuid4(),
            request_id=req.id,
            status="pending",
            sla_deadline=future_deadline,
        )
        req.status = "queued_for_review"
        db_session.add(item)
        db_session.add(req)
        await db_session.flush()

        timed_out = await handle_sla_timeouts(db_session)

        assert not any(t.id == item.id for t in timed_out)
        assert item.status == "pending"
