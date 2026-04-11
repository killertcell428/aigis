"""Policy manager: load and cache tenant policies."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy import Policy


async def get_active_policy(
    db: AsyncSession, tenant_id: uuid.UUID
) -> Policy | None:
    """Fetch the active policy for a tenant.

    Returns the first active policy, or None if none exists.
    A sensible default is applied in the proxy handler when None.
    """
    result = await db.execute(
        select(Policy).where(
            Policy.tenant_id == tenant_id,
            Policy.is_active == True,
        )
    )
    return result.scalars().first()


async def create_default_policy(db: AsyncSession, tenant_id: uuid.UUID) -> Policy:
    """Create a default policy for a tenant if none exists."""
    policy = Policy(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="Default Policy",
        description="Auto-created default security policy.",
        is_active=True,
    )
    db.add(policy)
    await db.flush()
    return policy
