"""Review queue router: list and process review items."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.review import ReviewItem
from app.models.user import User
from app.review.service import process_review_decision

router = APIRouter(prefix="/api/v1/review", tags=["review"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ReviewDecisionRequest(BaseModel):
    decision: str  # approve | reject | escalate
    note: str | None = None


class RequestDetail(BaseModel):
    model: str | None = None
    messages: list[dict] | None = None
    input_risk_score: int = 0
    input_risk_level: str = "low"
    input_matched_rules: list[dict] = []
    client_ip: str | None = None

    model_config = {"from_attributes": True}


class ReviewItemResponse(BaseModel):
    id: uuid.UUID
    request_id: uuid.UUID
    status: str
    sla_deadline: datetime
    decision: str | None
    reviewer_note: str | None
    created_at: datetime
    reviewed_at: datetime | None
    request_detail: RequestDetail | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/queue")
async def list_review_queue(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str = Query(default="pending", alias="status"),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    """List review items for the current user's tenant, including request details."""
    result = await db.execute(
        select(ReviewItem)
        .join(ReviewItem.request)
        .where(
            ReviewItem.request.has(tenant_id=current_user.tenant_id),
            ReviewItem.status == status_filter,
        )
        .options(selectinload(ReviewItem.request))
        .order_by(ReviewItem.sla_deadline.asc())
        .limit(limit)
        .offset(offset)
    )
    items = list(result.scalars().all())
    return [_item_to_response(item) for item in items]


def _item_to_response(item: ReviewItem) -> dict:
    """Convert ReviewItem + Request to response dict with request details."""
    resp = {
        "id": str(item.id),
        "request_id": str(item.request_id),
        "status": item.status,
        "sla_deadline": item.sla_deadline.isoformat() if item.sla_deadline else None,
        "decision": item.decision,
        "reviewer_note": item.reviewer_note,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
    }
    if item.request:
        resp["request_detail"] = {
            "model": item.request.model,
            "messages": item.request.messages,
            "input_risk_score": item.request.input_risk_score,
            "input_risk_level": item.request.input_risk_level,
            "input_matched_rules": item.request.input_matched_rules or [],
            "client_ip": item.request.client_ip,
        }
    return resp


@router.get("/queue/{item_id}", response_model=ReviewItemResponse)
async def get_review_item(
    item_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReviewItem:
    """Get a single review item with its associated request."""
    result = await db.execute(
        select(ReviewItem)
        .where(ReviewItem.id == item_id)
        .options(selectinload(ReviewItem.request))
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review item not found")

    # Tenant isolation check
    if item.request.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return item


@router.post("/queue/{item_id}/decide", response_model=ReviewItemResponse)
async def decide_review_item(
    item_id: uuid.UUID,
    body: ReviewDecisionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReviewItem:
    """Submit a review decision (approve / reject / escalate)."""
    # Role check: only admin or reviewer can make decisions
    if current_user.role not in ("admin", "reviewer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reviewer or admin role required to make review decisions",
        )

    if body.decision not in ("approve", "reject", "escalate"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="decision must be one of: approve, reject, escalate",
        )

    # Verify item belongs to this tenant
    result = await db.execute(
        select(ReviewItem)
        .where(ReviewItem.id == item_id)
        .options(selectinload(ReviewItem.request))
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Review item not found")
    if item.request.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        updated = await process_review_decision(
            db=db,
            review_item_id=item_id,
            reviewer_id=current_user.id,
            decision=body.decision,
            note=body.note,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return updated
