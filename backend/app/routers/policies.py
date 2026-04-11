"""Policies router: CRUD for tenant policies."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_admin_user, get_current_user
from app.models.policy import Policy
from app.models.user import User

router = APIRouter(prefix="/api/v1/policies", tags=["policies"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class CustomRule(BaseModel):
    id: str
    name: str
    pattern: str
    score_delta: int = Field(ge=0, le=100)
    enabled: bool = True


class PolicyCreateRequest(BaseModel):
    name: str
    description: str | None = None
    auto_allow_threshold: int = Field(default=30, ge=0, le=100)
    auto_block_threshold: int = Field(default=81, ge=0, le=100)
    review_sla_minutes: int = Field(default=30, ge=1, le=1440)
    sla_fallback: str = "block"
    custom_rules: list[CustomRule] = []


class PolicyUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
    auto_allow_threshold: int | None = Field(default=None, ge=0, le=100)
    auto_block_threshold: int | None = Field(default=None, ge=0, le=100)
    review_sla_minutes: int | None = Field(default=None, ge=1, le=1440)
    sla_fallback: str | None = None
    custom_rules: list[CustomRule] | None = None


class PolicyResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    auto_allow_threshold: int
    auto_block_threshold: int
    review_sla_minutes: int
    sla_fallback: str
    custom_rules: list

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("", response_model=list[PolicyResponse])
@router.get("/", response_model=list[PolicyResponse], include_in_schema=False)
async def list_policies(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[Policy]:
    result = await db.execute(
        select(Policy).where(Policy.tenant_id == current_user.tenant_id)
    )
    return list(result.scalars().all())


@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_policy(
    body: PolicyCreateRequest,
    current_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Policy:
    policy = Policy(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        name=body.name,
        description=body.description,
        auto_allow_threshold=body.auto_allow_threshold,
        auto_block_threshold=body.auto_block_threshold,
        review_sla_minutes=body.review_sla_minutes,
        sla_fallback=body.sla_fallback,
        custom_rules=[r.model_dump() for r in body.custom_rules],
    )
    db.add(policy)
    await db.flush()
    return policy


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Policy:
    result = await db.execute(
        select(Policy).where(
            Policy.id == policy_id, Policy.tenant_id == current_user.tenant_id
        )
    )
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.patch("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: uuid.UUID,
    body: PolicyUpdateRequest,
    current_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Policy:
    result = await db.execute(
        select(Policy).where(
            Policy.id == policy_id, Policy.tenant_id == current_user.tenant_id
        )
    )
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")

    updates = body.model_dump(exclude_none=True)
    if "custom_rules" in updates:
        updates["custom_rules"] = [r.model_dump() for r in body.custom_rules]
    for key, val in updates.items():
        setattr(policy, key, val)

    db.add(policy)
    return policy


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    result = await db.execute(
        select(Policy).where(
            Policy.id == policy_id, Policy.tenant_id == current_user.tenant_id
        )
    )
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    await db.delete(policy)
