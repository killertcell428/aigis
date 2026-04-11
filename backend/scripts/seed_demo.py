"""Seed script for demo environment.

Creates a demo tenant, admin user, reviewer user, default policy, and API key.
Idempotent — skips if demo data already exists.

Usage:
    python -m scripts.seed_demo
"""
import asyncio
import sys
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure app package is importable
sys.path.insert(0, ".")

from app.auth.api_keys import generate_api_key
from app.auth.jwt import hash_password
from app.db.session import AsyncSessionLocal, engine
from app.models.policy import Policy
from app.models.tenant import Tenant
from app.models.user import User


DEMO_TENANT_SLUG = "acme-corp"
DEMO_ADMIN_EMAIL = "admin@demo.com"
DEMO_REVIEWER_EMAIL = "reviewer@demo.com"
DEMO_PASSWORD = "demo1234"


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        # Check if demo tenant exists
        result = await db.execute(
            select(Tenant).where(Tenant.slug == DEMO_TENANT_SLUG)
        )
        tenant = result.scalar_one_or_none()

        if tenant:
            print(f"[SKIP] Demo tenant '{DEMO_TENANT_SLUG}' already exists.")
            # Still print API key info for admin
            admin_result = await db.execute(
                select(User).where(User.email == DEMO_ADMIN_EMAIL)
            )
            admin = admin_result.scalar_one_or_none()
            if admin and admin.api_key_hash:
                print(f"\n  Login:  {DEMO_ADMIN_EMAIL} / ********")
                print("  API Key: (already generated — check previous seed output)")
            return

        # 1. Create tenant
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Acme Corp",
            slug=DEMO_TENANT_SLUG,
            is_active=True,
        )
        db.add(tenant)
        await db.flush()
        print(f"[OK] Tenant created: {tenant.name} ({tenant.id})")

        # 2. Create admin user
        admin = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email=DEMO_ADMIN_EMAIL,
            hashed_password=hash_password(DEMO_PASSWORD),
            full_name="Demo Admin",
            role="admin",
            is_active=True,
        )

        # Generate API key for proxy requests
        raw_key, hashed_key = generate_api_key()
        admin.api_key_hash = hashed_key

        db.add(admin)
        print(f"[OK] Admin user created: {admin.email}")

        # 3. Create reviewer user
        reviewer = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email=DEMO_REVIEWER_EMAIL,
            hashed_password=hash_password(DEMO_PASSWORD),
            full_name="Demo Reviewer",
            role="reviewer",
            is_active=True,
        )
        db.add(reviewer)
        print(f"[OK] Reviewer user created: {reviewer.email}")

        # 4. Create default policy
        policy = Policy(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name="Default Security Policy",
            description="Standard security policy with balanced thresholds.",
            is_active=True,
            auto_allow_threshold=30,
            auto_block_threshold=81,
            review_sla_minutes=30,
            sla_fallback="block",
            custom_rules=[],
        )
        db.add(policy)
        print(f"[OK] Default policy created: {policy.name}")

        await db.commit()

        # Print credentials — mask sensitive values in logs.
        # The API key is shown once at initial seed only.
        masked_key = raw_key[:8] + "..." + raw_key[-4:]
        print("\n" + "=" * 60)
        print("  Aigis Demo — Ready!")
        print("=" * 60)
        print(f"\n  Dashboard Login:")
        print(f"    Admin:    {DEMO_ADMIN_EMAIL} / ********")
        print(f"    Reviewer: {DEMO_REVIEWER_EMAIL} / ********")
        print(f"\n  API Key (for proxy requests):")
        print(f"    {masked_key}")
        print(f"\n  Full API key written to: .aigis/demo_api_key")
        print(f"\n  Use in code:")
        print(f'    client = OpenAI(api_key="<your-api-key>",')
        print(f'                    base_url="http://localhost:8000/api/v1/proxy")')
        print("=" * 60)

        # Write full key to file instead of logging it
        key_dir = __import__("pathlib").Path(".aigis")
        key_dir.mkdir(parents=True, exist_ok=True)
        key_file = key_dir / "demo_api_key"
        key_file.write_text(raw_key)
        try:
            key_file.chmod(0o600)
        except OSError:
            pass


async def main() -> None:
    try:
        await seed()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
