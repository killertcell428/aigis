"""Review queue service: create, fetch, and process review items."""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.logger import log_event
from app.models.incident import Incident
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
    # Use FOR UPDATE to prevent concurrent review decisions (race condition)
    result = await db.execute(
        select(ReviewItem)
        .where(ReviewItem.id == review_item_id)
        .options(selectinload(ReviewItem.request))
        .with_for_update()
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

    replay_response = None

    if decision == "approve":
        item.status = "approved"
        request.status = "allowed"
        event_type = "review.approved"
        severity = "info"

        # Replay: forward the original request to LLM
        replay_response = await _replay_approved_request(request)

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
        details={
            "decision": decision,
            "note": note,
            "replay_success": replay_response is not None if decision == "approve" else None,
        },
    )

    # Update linked incident if exists
    inc_result = await db.execute(
        select(Incident).where(Incident.request_id == request.id)
    )
    incident = inc_result.scalar_one_or_none()
    if incident:
        from app.incidents.service import add_timeline_entry
        resolution_map = {"approve": "approved", "reject": "rejected", "escalate": "escalated"}
        incident.resolution = resolution_map.get(decision, decision)
        incident.resolution_note = note
        if decision in ("approve", "reject"):
            incident.status = "mitigated"
            incident.resolved_at = now
            if incident.sla_deadline:
                incident.sla_met = now <= incident.sla_deadline
        add_timeline_entry(
            incident,
            action=f"review:{decision}",
            actor=str(reviewer_id),
            detail=note or f"Review decision: {decision}",
        )
        db.add(incident)

    return item


async def _replay_approved_request(request: Request) -> dict | None:
    """Forward approved request to upstream LLM and store the response.

    Applies output filter on the response to prevent data leakage.
    Returns the LLM response body on success, None on failure.
    """
    import logging
    from app.config import settings
    from app.filters.output_filter import filter_output
    from app.proxy.handler import _forward_to_upstream

    logger = logging.getLogger(__name__)

    request_body = {
        "model": request.model,
        "messages": request.messages,
    }

    try:
        response_body, status_code = await _forward_to_upstream(
            request_body=request_body,
            api_key=settings.openai_api_key,
        )

        # Run output filter on replay response (security: prevent data leakage)
        if status_code == 200:
            output_result = filter_output(response_body, [])
            if output_result.risk_score >= 80:
                logger.warning(
                    "Replay response blocked by output filter for request %s (score=%d)",
                    request.id, output_result.risk_score,
                )
                request.status = "blocked"
                request.response_body = {"error": "Response blocked by output filter after replay"}
                request.response_status_code = 403
                return None

        request.response_body = response_body
        request.response_status_code = status_code
        return response_body
    except Exception as exc:
        logger.exception("Replay failed for request %s: %s", request.id, exc)
        return None


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
