"""Review queue service: create, fetch, and process review items."""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.logger import log_event
from app.models.request import Request
from app.models.review import ReviewItem


async def enqueue_for_review(
    db: AsyncSession,
    request: Request,
    sla_minutes: int,
) -> ReviewItem:
    """Add a request to the human review queue.

    Sets the SLA deadline and creates a ReviewItem record.
    """
    sla_deadline = datetime.now(timezone.utc) + timedelta(minutes=sla_minutes)
    item = ReviewItem(
        id=uuid.uuid4(),
        request_id=request.id,
        status="pending",
        sla_deadline=sla_deadline,
    )
    db.add(item)

    request.status = "queued_for_review"
    db.add(request)

    await db.flush()

    await log_event(
        db=db,
        tenant_id=request.tenant_id,
        event_type="request.queued",
        summary=f"Request queued for human review (score={request.input_risk_score})",
        request_id=request.id,
        severity="warning",
        details={
            "risk_score": request.input_risk_score,
            "risk_level": request.input_risk_level,
            "sla_deadline": sla_deadline.isoformat(),
        },
    )
    return item


async def process_review_decision(
    db: AsyncSession,
    review_item_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    decision: str,
    note: str | None = None,
) -> ReviewItem:
    """Apply a reviewer's decision to a review item.

    Args:
        decision: "approve" | "reject" | "escalate"
    """
    result = await db.execute(
        select(ReviewItem)
        .where(ReviewItem.id == review_item_id)
        .options(selectinload(ReviewItem.request))
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise ValueError(f"ReviewItem {review_item_id} not found")
    if item.status != "pending":
        raise ValueError(f"ReviewItem is already {item.status}")

    now = datetime.now(timezone.utc)
    item.reviewer_id = reviewer_id
    item.decision = decision
    item.reviewer_note = note
    item.reviewed_at = now

    request = item.request

    if decision == "approve":
        item.status = "approved"
        request.status = "allowed"
        event_type = "review.approved"
        severity = "info"
    elif decision == "reject":
        item.status = "rejected"
        request.status = "blocked"
        event_type = "review.rejected"
        severity = "warning"
    else:  # escalate
        item.status = "escalated"
        request.status = "escalated"
        event_type = "review.escalated"
        severity = "critical"

    db.add(item)
    db.add(request)

    await log_event(
        db=db,
        tenant_id=request.tenant_id,
        event_type=event_type,
        summary=f"Review {decision}d by reviewer",
        request_id=request.id,
        actor_id=reviewer_id,
        severity=severity,
        details={"decision": decision, "note": note},
    )
    return item


async def handle_sla_timeouts(db: AsyncSession) -> list[ReviewItem]:
    """Find review items past their SLA deadline and apply the fallback action.

    Intended to be called periodically by a background task.
    """
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ReviewItem)
        .where(ReviewItem.status == "pending", ReviewItem.sla_deadline < now)
        .options(selectinload(ReviewItem.request))
    )
    timed_out: list[ReviewItem] = []

    for item in result.scalars().all():
        request = item.request
        # Determine fallback from policy (passed via request metadata)
        # Default: block
        item.status = "timed_out"
        item.decision = "timed_out"
        request.status = "blocked"
        db.add(item)
        db.add(request)

        await log_event(
            db=db,
            tenant_id=request.tenant_id,
            event_type="review.timed_out",
            summary="Review SLA expired — request blocked by fallback policy",
            request_id=request.id,
            severity="critical",
            details={"sla_deadline": item.sla_deadline.isoformat()},
        )
        timed_out.append(item)

    return timed_out
