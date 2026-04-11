"""Pytest configuration and fixtures for Aigis backend tests."""
import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.jwt import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.policy import Policy
from app.models.tenant import Tenant
from app.models.user import User

# Use an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# SQLite doesn't support JSONB — map it to SQLite's JSON compiler for tests
SQLiteTypeCompiler.visit_JSONB = SQLiteTypeCompiler.visit_JSON


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional test database session."""
    TestSession = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with TestSession() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    """Create a test tenant."""
    t = Tenant(id=uuid.uuid4(), name="Test Corp", slug=f"test-{uuid.uuid4().hex[:8]}")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, tenant: Tenant) -> User:
    """Create a test admin user."""
    u = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email=f"admin-{uuid.uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("password123"),
        full_name="Test Admin",
        role="admin",
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest_asyncio.fixture
async def reviewer_user(db_session: AsyncSession, tenant: Tenant) -> User:
    """Create a test reviewer user."""
    u = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email=f"reviewer-{uuid.uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("password123"),
        full_name="Test Reviewer",
        role="reviewer",
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest_asyncio.fixture
async def policy(db_session: AsyncSession, tenant: Tenant) -> Policy:
    """Create a default policy for the test tenant."""
    p = Policy(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name="Test Policy",
        is_active=True,
        auto_allow_threshold=30,
        auto_block_threshold=81,
        review_sla_minutes=30,
        sla_fallback="block",
        custom_rules=[],
    )
    db_session.add(p)
    await db_session.flush()
    return p


@pytest_asyncio.fixture
async def admin_token(admin_user: User, tenant: Tenant) -> str:
    """Generate a JWT token for the admin user."""
    return create_access_token(
        subject=str(admin_user.id),
        tenant_id=str(tenant.id),
        role="admin",
    )


@pytest_asyncio.fixture
async def reviewer_token(reviewer_user: User, tenant: Tenant) -> str:
    """Generate a JWT token for the reviewer user."""
    return create_access_token(
        subject=str(reviewer_user.id),
        tenant_id=str(tenant.id),
        role="reviewer",
    )


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP test client with DB dependency override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
